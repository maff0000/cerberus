"""Offline tests for the WO-1.2b ingestion layer (no network, no clock dependence).

Run with the rest of the suite: ``python3 -m pytest`` (pyproject adds ``src`` and ``.``).
"""

from __future__ import annotations

from datetime import date, datetime, timezone
from pathlib import Path

import pytest
import yaml

from crash_detector.collectors import DelayKind, RetryPolicy, collect
from crash_detector.collectors.adapter import AdapterFetchError
from crash_detector.collectors.validation import JsonSchemaValidator, SchemaRejection
from crash_detector.observations import OK, FetchFailed, Malformed
from ingestion import adapters as A
from ingestion.catalog import (EGRESS_HOSTS, INGREDIENTS, NON_HTTP_PEERS, NOT_TRACTABLE, PARTIAL,
                               SUBSTITUTED_FEEDS, build_adapter)
from ingestion.report import indicator_states
from ingestion.store import SqliteStore

ROOT = Path(__file__).resolve().parents[1]
MAPPING = yaml.safe_load((ROOT / "governance/mapping/indicator_mapping.yaml").read_text())["indicators"]
NOW = datetime(2026, 10, 11, 12, 0, tzinfo=timezone.utc)
POLICY = RetryPolicy(max_attempts=1, timeout_seconds=5.0, backoff_seconds=0.0)


# --- catalog vs the ratified mapping ---------------------------------------------------- #


def test_every_ratified_indicator_is_served_or_listed_not_tractable_never_both():
    ids = {row["id"] for row in MAPPING}
    served = {i for ing in INGREDIENTS for i in ing.serves}
    assert len(ids - {"constituent_breadth_200dma"}) == 30  # the 30 ratified rows; WO-1.10 added exactly one, named here
    assert "constituent_breadth_200dma" in ids
    assert served | set(NOT_TRACTABLE) == ids
    assert not served & set(NOT_TRACTABLE)


def test_no_ingredient_invents_an_indicator_or_a_partial_for_an_unserved_one():
    ids = {row["id"] for row in MAPPING}
    assert {i for ing in INGREDIENTS for i in ing.serves} <= ids
    assert set(PARTIAL) <= {i for ing in INGREDIENTS for i in ing.serves}


def test_declared_feeds_name_a_feed_the_mapping_row_actually_declares():
    feeds = {row["id"]: row["source"]["feed"] for row in MAPPING}
    for ing in INGREDIENTS:
        for ind in ing.serves:
            if ind in SUBSTITUTED_FEEDS:  # a recorded, authority-cited substitute (WO-1.6): see its own test
                continue
            # every FRED series / CBOE index token an ingredient uses appears in the row's feed
            token = ing.ref if ing.kind in ("fred", "cboe") else None
            if token:
                assert token in feeds[ind], (ing.source_id, ind, feeds[ind])


def test_every_declared_input_of_a_derived_indicator_is_ingested():
    """gold_real_rate_cross needs GC and DFII10; vix_term_structure needs VIX and VIX3M."""
    serving = lambda ind: {i.ref for i in INGREDIENTS if ind in i.serves}  # noqa: E731
    # WO-1.7: gold is the LBMA fix, NOT the COMEX futures; the futures close must not feed it silently.
    assert {"gold_pm+gold_am", "DFII10"} <= serving("gold_real_rate_cross") and "GC=F" not in serving("gold_real_rate_cross")
    assert {"GACDFSA066MSFRBPHI", "GACDISA066MSFRBNY", "BACTSAMFRBDAL"} <= serving("ism_manufacturing")
    assert {"DRTSCILM", "DRTSCIS"} <= serving("sloos_bank_lending")
    assert {"VIX", "VIX3M"} <= serving("vix_term_structure")
    assert {"HYG", "LQD"} <= serving("credit_stress_hyg_lqd")
    assert {"RSP", "SPY"} <= serving("breadth_rsp_spy")
    assert {"HG=F", "GC=F"} <= serving("copper_gold")


def test_adapter_urls_reach_only_registered_egress_hosts_and_registry_matches():
    from urllib.parse import urlsplit

    # WO-1.12: the HERMES ingredient's transport is a Redis GET, not HTTP. It has no ``_url`` and is
    # therefore NOT an egress host. It is excluded BY KIND AND NAMED, not skipped by a try/except, so a
    # SECOND non-HTTP transport cannot be added silently — the two assertions below fail until it is
    # declared in NON_HTTP_PEERS and listed here too.
    non_http = [i for i in INGREDIENTS if i.kind == "hermes"]
    assert [i.source_id for i in non_http] == ["hermes.xau_usd.h4_close"]
    assert len(NON_HTTP_PEERS) == len(non_http)
    assert all(f"{A.HERMES_PEER[0]}:{A.HERMES_PEER[1]}" in peer for peer in NON_HTTP_PEERS)

    hosts = {urlsplit(build_adapter(i, lambda: NOW)._url()).hostname
             for i in INGREDIENTS if i.kind not in ("manual", "hermes")}
    assert hosts == set(EGRESS_HOSTS)
    registry = yaml.safe_load((ROOT / "deploy/egress-destinations.yaml").read_text())["destinations"]
    assert {d["host"] for d in registry} == hosts
    # The LAN peer is absent from BOTH the HTTP allowlist and the destination registry, deliberately:
    # that registry refuses an address literal by design (CD-ASR-F04). See catalog.NON_HTTP_PEERS.
    assert A.HERMES_PEER[0] not in hosts and A.HERMES_PEER[0] not in {d["host"] for d in registry}


def test_source_ids_are_unique():
    ids = [i.source_id for i in INGREDIENTS]
    assert len(ids) == len(set(ids))


# --- pure parsers ----------------------------------------------------------------------- #


def test_fred_takes_latest_non_missing_row_and_skips_dot():
    body = "observation_date,DFF\n2026-10-06,3.9\n2026-10-07,3.88\n2026-10-08,.\n"
    assert A.parse_fred_csv(body, "DFF", "percent") == {"unit": "percent", "observation_date": "2026-10-07", "value": 3.88}


def test_fred_wrong_series_header_is_malformed_not_read():
    assert "unit" not in A.parse_fred_csv("observation_date,OTHER\n2026-10-06,1\n", "DFF", "percent")


def test_fred_all_missing_is_empty_not_zero():
    out = A.parse_fred_csv("observation_date,DFF\n2026-10-06,.\n", "DFF", "percent")
    assert out == {"unit": "percent"}


def test_fred_garbage_value_is_passed_through_for_schema_to_reject():
    out = A.parse_fred_csv("observation_date,DFF\n2026-10-06,abc\n", "DFF", "percent")
    assert out["value"] == "abc"


def test_fred_nan_is_not_a_number():
    assert A.parse_fred_csv("observation_date,DFF\n2026-10-06,nan\n", "DFF", "p")["value"] == "nan"


# WO-1.15. ``parse_fred_csv_for_date`` asks a different question of the SAME body than the
# five tests above: not "what is this series' current value" — the LATEST row — but "what was
# the value for date D", which is the row dated D or nothing at all. The two parsers must not
# be able to stand in for each other, so the first test below pins both against one body.


def test_fred_for_date_reads_the_row_dated_exactly_that_date_and_not_the_latest_one():
    """The whole point: the LATEST row is present, carries a different figure, and is not it."""
    body = "observation_date,DFF\n1999-01-01,4.63\n2005-06-15,3.04\n2026-10-13,3.88\n"
    assert A.parse_fred_csv_for_date(body, "DFF", "percent", "2005-06-15") == {
        "unit": "percent", "observation_date": "2005-06-15", "value": 3.04}
    # parse_fred_csv, asked of the same body, answers for the last row instead. Both are
    # right about their own question, which is why there are two functions.
    assert A.parse_fred_csv(body, "DFF", "percent")["observation_date"] == "2026-10-13"


def test_fred_for_date_matches_the_key_even_when_the_body_was_never_filtered():
    """A window wholly before a series' first observation is IGNORED by plain FRED and the
    WHOLE series comes back (``evidence/wo115_fred_window_probe.json``, case
    ``q2_window_before_series_start``). Reading such a body by POSITION — the last row, or
    "the only row" — answers a 1944 backfill with this morning's rate. Exact-key matching is
    what makes that body harmless: it carries the date or it does not."""
    whole_series = "observation_date,DFF\n1954-07-01,1.13\n1954-07-02,1.25\n2026-10-13,3.88\n"
    assert A.parse_fred_csv_for_date(whole_series, "DFF", "percent", "1944-07-01") == {
        "unit": "percent"}
    assert A.parse_fred_csv_for_date(whole_series, "DFF", "percent", "1954-07-02") == {
        "unit": "percent", "observation_date": "1954-07-02", "value": 1.25}


def test_fred_for_date_has_no_row_for_the_date_is_empty_not_a_neighbouring_row():
    body = "observation_date,T5YIE\n2015-06-19,1.63\n2015-06-22,1.65\n"
    assert A.parse_fred_csv_for_date(body, "T5YIE", "percent", "2015-06-20") == {"unit": "percent"}


def test_fred_for_date_dot_for_no_data_on_the_matched_row_is_empty_not_zero():
    """FRED writes ``.`` for no data, and so the series HAS this date and published nothing
    for it. EMPTY — and emphatically not the next row down, which does carry a figure."""
    body = "observation_date,T5YIE\n2026-10-12,.\n2026-10-13,2.33\n"
    assert A.parse_fred_csv_for_date(body, "T5YIE", "percent", "2026-10-12") == {"unit": "percent"}
    assert A.parse_fred_csv_for_date("observation_date,T5YIE\n2026-10-12,\n", "T5YIE", "percent",
                                     "2026-10-12") == {"unit": "percent"}


@pytest.mark.parametrize("body,expected", [
    ("", "header"),
    ("nonsense", "header"),
    ("observation_date,DFF,extra\n2005-06-15,3.04\n", "header"),
    ("DATE,DFF\n2005-06-15,3.04\n", "header"),
    ("observation_date,OTHER\n2005-06-15,3.04\n", "series"),
])
def test_fred_for_date_an_unreadable_body_is_malformed_never_an_absent_observation(body, expected):
    """MALFORMED and EMPTY are different answers: the first says we cannot read what arrived,
    the second says the source has no figure. No ``unit`` key, so the closed response schema
    rejects it rather than a reading being admitted with no value."""
    out = A.parse_fred_csv_for_date(body, "DFF", "percent", "2005-06-15")
    assert out == {"malformed": expected} and "unit" not in out


def test_fred_for_date_a_garbage_value_is_passed_through_for_the_schema_to_reject():
    """Exactly as ``parse_fred_csv`` does: the raw token is carried, never defaulted."""
    out = A.parse_fred_csv_for_date("observation_date,DFF\n2005-06-15,abc\n", "DFF", "percent",
                                    "2005-06-15")
    assert out["value"] == "abc"


def test_cboe_date_and_column():
    body = "DATE,OPEN,CLOSE\n10/08/2026,1,2\n10/09/2026,3,14.84\n"
    assert A.parse_cboe_csv(body, "CLOSE", "index") == {"unit": "index", "observation_date": "2026-10-09", "value": 14.84}


def test_cboe_missing_column_is_malformed():
    assert "unit" not in A.parse_cboe_csv("DATE,X\n10/09/2026,1\n", "CLOSE", "index")



# WO-1.16. ``parse_cboe_csv_for_date`` asks of the SAME body the question the two tests above
# do not: not "what is this index at now" — the LATEST row — but "what was it on date D". The
# bodies below are real: every row is copied verbatim out of
# ``evidence/wo116_cboe_probe.json``'s ``rows_for_month_verbatim`` (2015-06) and
# ``rows_tail``, so the shape under test is the shape the endpoint actually serves.

#: VIX_History.csv, header verbatim, four 2015-06 sessions and the four latest ones, exactly as
#: probed. A per-date request gets the WHOLE history back — CBOE honours no window — so the
#: last row of this body is what a position read would wrongly answer a 2015 backfill with.
_CBOE_VIX_BODY = (
    "DATE,OPEN,HIGH,LOW,CLOSE\n"
    "06/11/2015,13.040000,13.220000,12.560000,12.850000\n"
    "06/12/2015,13.310000,14.020000,13.300000,13.780000\n"
    "06/15/2015,15.480000,15.570000,14.910000,15.390000\n"
    "06/16/2015,15.620000,15.620000,14.810000,14.810000\n"
    "10/13/2026,15.610000,15.610000,15.170000,15.270000\n"
    "10/14/2026,15.170000,17.450000,14.980000,16.870000\n"
)


def test_cboe_for_date_reads_the_row_dated_exactly_that_date_and_not_the_latest_one():
    """The whole point: the latest row is present, carries a different figure, and is not it."""
    assert A.parse_cboe_csv_for_date(_CBOE_VIX_BODY, "CLOSE", "index", "2015-06-15") == {
        "unit": "index", "observation_date": "2015-06-15", "value": 15.39}
    # parse_cboe_csv, asked of the same body, answers for the last row instead. Both are
    # right about their own question, which is why there are two functions.
    assert A.parse_cboe_csv(_CBOE_VIX_BODY, "CLOSE", "index")["observation_date"] == "2026-10-14"


def test_cboe_for_date_matches_the_converted_date_and_never_the_raw_mm_dd_yyyy_cell():
    """The one thing that differs from FRED: ``DATE`` is ``MM/DD/YYYY``, the key asked for is
    ISO. The row's raw cell reads ``06/15/2015`` and no ISO string will ever equal it, so a
    comparison against the raw cell answers EMPTY for a date the body plainly carries. Pinned
    both ways: the ISO key matches, and the raw spelling of that same date matches nothing."""
    assert A.parse_cboe_csv_for_date(_CBOE_VIX_BODY, "CLOSE", "index", "2015-06-15")["value"] == 15.39
    assert A.parse_cboe_csv_for_date(_CBOE_VIX_BODY, "CLOSE", "index", "06/15/2015") == {"unit": "index"}


def test_cboe_for_date_a_date_with_no_row_is_empty_not_a_neighbouring_session():
    """CBOE publishes NO missing-data marker — no FRED-style ``.``, no blank cells: every row
    of every probed body carries a figure in every column (``unreadable_date_cells: 0``), and
    non-sessions are simply ABSENT. 2015-06-13 and 06-14 were a weekend and have no rows at
    all, so "the source has no figure for this date" arrives here as an unmatched date, which
    is why this is the EMPTY case that matters for CBOE rather than a missing-value one."""
    assert A.parse_cboe_csv_for_date(_CBOE_VIX_BODY, "CLOSE", "index", "2015-06-13") == {"unit": "index"}
    # Before the index existed, and after the body's last session: same answer, never a row.
    assert A.parse_cboe_csv_for_date(_CBOE_VIX_BODY, "CLOSE", "index", "1985-01-02") == {"unit": "index"}
    assert A.parse_cboe_csv_for_date(_CBOE_VIX_BODY, "CLOSE", "index", "2026-10-15") == {"unit": "index"}


def test_cboe_for_date_an_empty_cell_on_the_matched_row_would_be_empty_not_zero():
    """Defensive, and labelled as such: no probed CBOE body carries a blank cell. If one ever
    does, the matched row has no figure and that is EMPTY — emphatically not zero, and not the
    next session down, which does carry one."""
    body = "DATE,OPEN,CLOSE\n06/15/2015,15.480000,\n06/16/2015,15.620000,14.810000\n"
    assert A.parse_cboe_csv_for_date(body, "CLOSE", "index", "2015-06-15") == {"unit": "index"}


@pytest.mark.parametrize("body,expected", [
    ("", "header"),
    ("nonsense", "header"),
    ("observation_date,CLOSE\n06/15/2015,15.39\n", "header"),
    ("DATE,OPEN,HIGH,LOW\n06/15/2015,15.48,15.57,14.91\n", "column"),
    ("DATE,SKEW\n06/15/2015,119.250000\n", "column"),
])
def test_cboe_for_date_an_unreadable_body_is_malformed_never_an_absent_observation(body, expected):
    """MALFORMED and EMPTY are different answers: the first says we cannot read what arrived,
    the second says the source has no figure for the date. No ``unit`` key, so the closed
    response schema rejects it rather than a reading being admitted with no value."""
    out = A.parse_cboe_csv_for_date(body, "CLOSE", "index", "2015-06-15")
    assert out == {"malformed": expected} and "unit" not in out


def test_cboe_for_date_a_garbage_value_is_passed_through_for_the_schema_to_reject():
    """Exactly as ``parse_cboe_csv`` does: the raw token is carried, never defaulted."""
    out = A.parse_cboe_csv_for_date("DATE,CLOSE\n06/15/2015,abc\n", "CLOSE", "index", "2015-06-15")
    assert out["value"] == "abc"


def test_cboe_for_date_reads_a_single_column_body_by_name():
    """SKEW_History.csv is ``DATE,SKEW`` — the column asked for is not always the fifth."""
    body = "DATE,SKEW\n06/12/2015,119.260000\n06/15/2015,119.250000\n10/14/2026,157.300000\n"
    assert A.parse_cboe_csv_for_date(body, "SKEW", "index", "2015-06-15") == {
        "unit": "index", "observation_date": "2015-06-15", "value": 119.25}

def test_yahoo_skips_null_closes_and_never_fills():
    body = '{"chart":{"result":[{"timestamp":[1791244800,1791331200],"indicators":{"quote":[{"close":[10.5,null]}]}}]}}'
    out = A.parse_yahoo_chart(body, "usd")
    assert out["value"] == 10.5 and out["observation_date"] == "2026-10-06"


def test_yahoo_history_is_raw_closes_only():
    body = '{"chart":{"result":[{"timestamp":[1791244800,1791331200],"indicators":{"quote":[{"close":[10.5,11.5]}]}}]}}'
    assert A.parse_yahoo_chart(body, "usd", 5)["history"] == [["2026-10-06", 10.5], ["2026-10-07", 11.5]]


@pytest.mark.parametrize("body", ["not json", "{}", '{"chart":{"result":null}}',
                                  '{"chart":{"result":[{"timestamp":[1],"indicators":{"quote":[{"close":[1,2]}]}}]}}'])
def test_yahoo_bad_shapes_are_malformed(body):
    assert "unit" not in A.parse_yahoo_chart(body, "usd")


# WO-1.16. ``parse_yahoo_chart_for_date`` asks of a Yahoo v8 chart body the question the three
# tests above do not: not "what is this symbol at NOW" — the LAST bar — but "what did it close
# at on date D", which is the bar dated D or nothing at all. It sits beside ``parse_yahoo_chart``
# for the reason ``parse_fred_csv_for_date`` and ``parse_cboe_csv_for_date`` sit beside their own
# latest-row parsers, and the two bodies below are REAL: both are copied verbatim out of
# ``evidence/wo116_yahoo_window_probe.json`` (probed 2026-10-15), so the shapes under test are the
# shapes the endpoint actually serves for a one-day window — on a trading day, and on a day the
# symbol did not print.
#: SPY, ``period1=1433721600&period2=1433807999&interval=1d`` — the whole UTC day of
#: 2015-06-08 — answered VERBATIM (``q2_window_one_day_utc_day``). ONE bar, stamped
#: 1433770200 = 2015-06-08T13:30Z (the session OPEN, not midnight), close 208.47999572753906.
#: ``meta`` and the ``adjclose`` block are kept exactly as served: the parser has to reach
#: past both, and a hand-trimmed body would not prove that.
_YAHOO_SPY_ONE_UTC_DAY = (
    '{"chart":{"result":[{"meta":{"currency":"USD","symbol":"SPY","exchangeName":"PCX","fullExcha'
    'ngeName":"NYSEArca","instrumentType":"ETF","firstTradeDate":728317800,"regularMarketTime":17'
    '92089976,"hasPrePostMarketData":true,"gmtoffset":-14400,"timezone":"EDT","exchangeTimezoneNa'
    'me":"America/New_York","regularMarketPrice":770.01,"regularMarketChangePercent":0.053,"fulld'
    'ayPrice":770.01,"fulldayChange":0.41,"fulldayChangePercent":0.053,"fiftyTwoWeekHigh":781.62,'
    '"fiftyTwoWeekLow":629.28,"regularMarketDayHigh":771.91,"regularMarketDayLow":764.44,"regular'
    'MarketVolume":26568391,"longName":"State Street SPDR S&P 500 ETF Trust","shortName":"State S'
    'treet SPDR S&P 500 ETF T","chartPreviousClose":209.77,"priceHint":2,"currentTradingPeriod":{'
    '"pre":{"timezone":"EDT","start":1792051200,"end":1792071000,"gmtoffset":-14400},"regular":{"'
    'timezone":"EDT","start":1792071000,"end":1792094400,"gmtoffset":-14400},"post":{"timezone":"'
    'EDT","start":1792094400,"end":1792108800,"gmtoffset":-14400}},"dataGranularity":"1d","range"'
    ':"","validRanges":["1d","5d","1mo","3mo","6mo","1y","2y","5y","10y","ytd","max"]},"timestamp'
    '":[1433770200],"indicators":{"quote":[{"close":[208.47999572753906],"high":[209.820007324218'
    '75],"low":[208.38999938964844],"volume":[89063300],"open":[209.63999938964844]}],"adjclose":'
    '[{"adjclose":[172.54739379882812]}]}}],"error":null}}'
)

#: SPY, the same one-day window on 2015-06-13 — a SATURDAY — answered VERBATIM
#: (``q3_window_on_non_trading_day``). HTTP 200, ``error: null``, ``meta`` complete, and the
#: bar arrays simply ABSENT: ``"quote":[{}]`` with NO ``timestamp`` key anywhere. This is the
#: shape of "the symbol did not print on this date", and it is the one shape the two Yahoo
#: parsers must answer DIFFERENTLY.
_YAHOO_SPY_NO_BAR_AT_ALL = (
    '{"chart":{"result":[{"meta":{"currency":"USD","symbol":"SPY","exchangeName":"PCX","fullExcha'
    'ngeName":"NYSEArca","instrumentType":"ETF","firstTradeDate":728317800,"regularMarketTime":17'
    '92089978,"hasPrePostMarketData":true,"gmtoffset":-14400,"timezone":"EDT","exchangeTimezoneNa'
    'me":"America/New_York","regularMarketPrice":770.01,"regularMarketChangePercent":0.053,"fulld'
    'ayPrice":770.01,"fulldayChange":0.41,"fulldayChangePercent":0.053,"fiftyTwoWeekHigh":781.62,'
    '"fiftyTwoWeekLow":629.28,"regularMarketDayHigh":771.91,"regularMarketDayLow":764.44,"regular'
    'MarketVolume":26568561,"longName":"State Street SPDR S&P 500 ETF Trust","shortName":"State S'
    'treet SPDR S&P 500 ETF T","chartPreviousClose":210.01,"priceHint":2,"currentTradingPeriod":{'
    '"pre":{"timezone":"EDT","end":1792071000,"start":1792051200,"gmtoffset":-14400},"regular":{"'
    'timezone":"EDT","end":1792094400,"start":1792071000,"gmtoffset":-14400},"post":{"timezone":"'
    'EDT","end":1792108800,"start":1792094400,"gmtoffset":-14400}},"dataGranularity":"1d","range"'
    ':"","validRanges":["1d","5d","1mo","3mo","6mo","1y","2y","5y","10y","ytd","max"]},"indicator'
    's":{"quote":[{}],"adjclose":[{}]}}],"error":null}}'
)

#: Not probed and not claimed to be: three bars, hand-built, to put OTHER dates in front of the
#: parser. The stamps are real session-open stamps (13:30Z, matching the probed bar above), and
#: the last one — 1791984600, 2026-10-14 — is lifted from the baseline ``range=10d`` case, i.e.
#: it is exactly what a body that ignored the window would end with (``q6_range_and_period_
#: together``: given ``range`` AND a window, range wins and the whole relative body comes back).
_YAHOO_BARS_FOR_OTHER_DATES = (
    '{"chart":{"result":[{"timestamp":[1433856600,1433943000,1791984600],'
    '"indicators":{"quote":[{"close":[207.0,208.0,769.5999755859375]}]}}],"error":null}}'
)


def test_yahoo_for_date_reads_the_bar_dated_exactly_that_date():
    """The probed one-day body, read whole: ``meta`` first, an ``adjclose`` block alongside the
    ``quote`` one, and the bar stamped at the session OPEN rather than at midnight."""
    assert A.parse_yahoo_chart_for_date(_YAHOO_SPY_ONE_UTC_DAY, "usd", "2015-06-08") == {
        "unit": "usd", "observation_date": "2015-06-08", "value": 208.47999572753906}
    # The date is derived from the STAMP, which is 13:30Z on the date asked for — so a parser
    # reading the stamp as anything but a UTC instant would answer for a different day.
    assert json.loads(_YAHOO_SPY_ONE_UTC_DAY)["chart"]["result"][0]["timestamp"] == [1433770200]
    assert datetime.fromtimestamp(1433770200, tz=timezone.utc).isoformat() == "2015-06-08T13:30:00+00:00"


def test_yahoo_for_date_a_null_close_on_the_matched_bar_is_empty_not_zero():
    """Yahoo nulls a session it has no print for, and ``parse_yahoo_chart``'s skip is KEPT here
    rather than assumed — asserted on both parsers against one body. Under an exact-date match a
    skipped bar cannot be replaced by a neighbouring one, so the bar being THERE with a null
    close falls out as EMPTY: no value, and emphatically not the other bar's close."""
    body = ('{"chart":{"result":[{"timestamp":[1433770200,1433856600],'
            '"indicators":{"quote":[{"close":[null,207.0]}]}}]}}')
    assert A.parse_yahoo_chart_for_date(body, "usd", "2015-06-08") == {"unit": "usd"}
    assert A.parse_yahoo_chart(body, "usd") == {
        "unit": "usd", "observation_date": "2015-06-09", "value": 207.0}  # skipped, never filled


def test_yahoo_for_date_an_absent_bar_array_is_empty_here_and_malformed_to_the_other_parser():
    """THE ONE SHAPE THE TWO PARSERS MUST ANSWER DIFFERENTLY, and the reason this function could
    not just reuse ``parse_yahoo_chart``'s shape checks wholesale.

    A one-day window on a non-trading day is answered ``200``, ``error: null``, ``meta`` intact,
    and the bar arrays simply ABSENT — ``"quote":[{}]`` and no ``timestamp`` key at all
    (``q3_window_on_non_trading_day``, SPY on Saturday 2015-06-13). ``parse_yahoo_chart`` reads
    that as MALFORMED, which is right for ITS question — the live loop asks for ``range=10d`` and
    a ten-day range with no bars in it is a body we cannot believe — and wrong for this one,
    where it is the ordinary answer "the symbol did not print on this date". Both verdicts are
    pinned here, against the one body, because each is only correct about its own question."""
    absent = json.loads(_YAHOO_SPY_NO_BAR_AT_ALL)["chart"]["result"][0]
    assert "timestamp" not in absent and absent["indicators"]["quote"] == [{}]  # the shape itself
    assert absent["meta"]["symbol"] == "SPY" and json.loads(_YAHOO_SPY_NO_BAR_AT_ALL)["chart"]["error"] is None

    assert A.parse_yahoo_chart(_YAHOO_SPY_NO_BAR_AT_ALL, "usd") == {"malformed": "shape"}
    assert A.parse_yahoo_chart_for_date(_YAHOO_SPY_NO_BAR_AT_ALL, "usd", "2015-06-13") == {"unit": "usd"}
    # EMPTY is not MALFORMED and not a value: the payload carries ``unit`` and nothing else, so
    # the store records an absent observation rather than an unreadable body.
    out = A.parse_yahoo_chart_for_date(_YAHOO_SPY_NO_BAR_AT_ALL, "usd", "2015-06-13")
    assert "malformed" not in out and "value" not in out and "observation_date" not in out


def test_yahoo_for_date_bars_for_other_dates_are_empty_and_never_a_neighbouring_bar():
    """A body full of bars nobody asked about is reachable — a caller that windowed wrongly, or
    not at all, since ``range=`` silently wins over a period window in the same URL. A POSITION
    read answers such a body with the LAST bar under the historical key asked for; an exact match
    cannot, and the two parsers are pinned against one body to show it."""
    for missing in ("2015-06-08", "2015-06-11", "2015-06-13", "2026-10-15"):
        assert A.parse_yahoo_chart_for_date(_YAHOO_BARS_FOR_OTHER_DATES, "usd", missing) == {"unit": "usd"}
    # The dates it DOES carry are matched, each to its own bar, never to the one next door.
    assert A.parse_yahoo_chart_for_date(_YAHOO_BARS_FOR_OTHER_DATES, "usd", "2015-06-09") == {
        "unit": "usd", "observation_date": "2015-06-09", "value": 207.0}
    assert A.parse_yahoo_chart_for_date(_YAHOO_BARS_FOR_OTHER_DATES, "usd", "2015-06-10") == {
        "unit": "usd", "observation_date": "2015-06-10", "value": 208.0}
    # parse_yahoo_chart, asked of the same body, answers with the last bar instead. Both are
    # right about their own question, which is why there are two functions.
    assert A.parse_yahoo_chart(_YAHOO_BARS_FOR_OTHER_DATES, "usd")["observation_date"] == "2026-10-14"


@pytest.mark.parametrize("body", [
    "not json",
    "",
    "{}",
    '{"chart":{}}',
    '{"chart":{"result":null}}',
    '{"chart":{"result":[]}}',
    '{"chart":{"result":[{"timestamp":[1433770200]}]}}',                      # no indicators
    '{"chart":{"result":[{"timestamp":[1433770200],"indicators":{"quote":[]}}]}}',
    # timestamp and close of different lengths: which close belongs to which bar is unknowable
    '{"chart":{"result":[{"timestamp":[1433770200],"indicators":{"quote":[{"close":[1,2]}]}}]}}',
    '{"chart":{"result":[{"timestamp":[1433770200,1433856600],"indicators":{"quote":[{"close":[1]}]}}]}}',
    # a stamp that is not a readable epoch second
    '{"chart":{"result":[{"timestamp":[100000000000000],"indicators":{"quote":[{"close":[1.0]}]}}]}}',
])
def test_yahoo_for_date_an_unreadable_body_is_malformed_never_an_absent_observation(body):
    """MALFORMED and EMPTY are different answers: the first says we cannot read what arrived, the
    second says the source has no figure for the date. No ``unit`` key, so the closed response
    schema rejects it rather than a reading being admitted with no value. Every shape here is one
    ``parse_yahoo_chart`` already rejects — only the ABSENT bar array above diverges."""
    out = A.parse_yahoo_chart_for_date(body, "usd", "2015-06-08")
    assert out == {"malformed": "shape"} and "unit" not in out


def test_yahoo_for_date_an_unreadable_stamp_is_malformed_rather_than_an_escaping_exception():
    """Why the iteration sits INSIDE the guard, unlike ``parse_yahoo_chart``'s: a stamp that is
    not an epoch second at all raises there, and an exception escaping into the collector is not
    an observation. Here it is MALFORMED, which is what an unreadable body is."""
    body = '{"chart":{"result":[{"timestamp":["nope"],"indicators":{"quote":[{"close":[1.0]}]}}]}}'
    assert A.parse_yahoo_chart_for_date(body, "usd", "2015-06-08") == {"malformed": "shape"}
    with pytest.raises(TypeError):
        A.parse_yahoo_chart(body, "usd")


def test_yahoo_for_date_a_garbage_value_is_passed_through_for_the_schema_to_reject():
    """Exactly as ``parse_yahoo_chart`` does: the raw token is carried, never defaulted."""
    body = '{"chart":{"result":[{"timestamp":[1433770200],"indicators":{"quote":[{"close":["abc"]}]}}]}}'
    assert A.parse_yahoo_chart_for_date(body, "usd", "2015-06-08")["value"] == "abc"


# --- WO-1.16: YahooChartAdapter's dated mode, which is the REQUEST half of the same change ---- #
#
# Two questions, one endpoint, and the second is opt-in. With ``observation_date`` left at None —
# every live call, since ``build_adapter`` has no argument that could set it — the adapter is the
# one it has always been. With a date set, the request REPLACES ``range`` with an absolute
# ``period1``/``period2`` window and the body is read by the exact-match parser above.


def _yahoo(symbol="SPY", history=0, field="close", getter=None, **kw):
    return A.YahooChartAdapter(
        symbol, history, field, source_id=f"yahoo.{symbol}", as_of_rule="obs_date", unit="usd",
        clock=lambda: NOW, **({} if getter is None else {"getter": getter}), **kw)


def test_yahoo_undated_adapter_builds_exactly_the_url_it_built_before_this_wo():
    """THE LIVE-LOOP NON-REGRESSION. Asserted as whole URLs rather than by substring: the undated
    request is not "still roughly right", it is character-for-character what it was. The first one
    is the URL the probe recorded as ``adapter_url_today`` for SPY before anything was changed."""
    chart = "https://query1.finance.yahoo.com/v8/finance/chart"
    assert _yahoo()._url() == f"{chart}/SPY?range=10d&interval=1d"
    assert _yahoo(history=5)._url() == f"{chart}/SPY?range=2y&interval=1d"
    assert _yahoo("^GSPC")._url() == f"{chart}/%5EGSPC?range=10d&interval=1d"
    assert _yahoo("HG=F", history=20)._url() == f"{chart}/HG%3DF?range=2y&interval=1d"
    # And nothing the CATALOG builds can be in the dated mode: every live yahoo wiring still asks
    # for a relative range and carries no window at all.
    live = [build_adapter(i, lambda: NOW) for i in INGREDIENTS if i.kind == "yahoo"]
    assert live, "the catalog serves no yahoo ingredient: this guard would pass vacuously"
    assert all("range=" in a._url() and "period1" not in a._url() for a in live)


def test_yahoo_dated_adapter_replaces_range_with_an_absolute_window_rather_than_appending_it():
    """``range`` and a window together is not a harmless belt-and-braces: given both, RANGE WINS
    and the whole relative body comes back (``q6_range_and_period_together``: ``range=2y`` plus a
    one-day window for 2015-06-08 answered 502 bars ending at that morning's). So ``range`` must
    be ABSENT, which is asserted as an absence — on the parsed keys and on the raw query text —
    not inferred from ``period1`` being present."""
    from urllib.parse import parse_qs, urlsplit

    url = _yahoo(observation_date="2015-06-08")._url()
    query = urlsplit(url).query
    assert set(parse_qs(query)) == {"period1", "period2", "interval"}
    assert "range" not in parse_qs(query) and "range" not in query
    assert parse_qs(query)["interval"] == ["1d"]
    # The history flag changes the RANGE, and in dated mode there is no range to change.
    # ``history`` picks the RANGE, and in dated mode there is no range for it to pick.
    assert _yahoo(history=20, observation_date="2015-06-08")._url() == url


def test_yahoo_dated_window_is_the_whole_utc_day_of_the_date_asked_for():
    """The window has to CONTAIN a bar stamped at the session open — 13:30Z or 14:30Z depending
    on the offset in force — so it is the whole UTC day: 00:00:00Z of D to 23:59:59Z of D.

    The two bounds are checked twice over, both times WITHOUT reusing the adapter's arithmetic.
    First against the integers in the probed URL itself, which is where they came from. Then,
    for four more dates, computed through ``calendar.timegm`` on a UTC struct_time — a different
    route to an epoch second than ``datetime(...).timestamp()`` — so an off-by-one in the
    adapter's "next midnight, minus a second" would show up here rather than be reproduced."""
    import calendar

    # The probed one-day window, verbatim from the URL in evidence/wo116_yahoo_window_probe.json.
    assert _yahoo(observation_date="2015-06-08")._url() == (
        "https://query1.finance.yahoo.com/v8/finance/chart/SPY"
        "?period1=1433721600&period2=1433807999&interval=1d")

    for iso in ("2015-06-08",   # the probed date, the same answer by the other route
                "2015-03-08",   # US DST begins: the session opens 14:30Z the day before, 13:30Z after
                "2015-11-01",   # and ends
                "2016-02-29",   # a leap day
                "1993-01-29"):  # SPY's first trade date, the left edge a backfill can reach
        year, month, day = (int(part) for part in iso.split("-"))
        first_second = calendar.timegm((year, month, day, 0, 0, 0, 0, 0, 0))
        last_second = calendar.timegm((year, month, day, 23, 59, 59, 0, 0, 0))
        assert f"period1={first_second}&period2={last_second}&interval=1d" in (
            _yahoo(observation_date=iso)._url()), iso
        # Not the zero-width encoding a caller reaches for first, which returns ZERO BARS for a
        # real trading day (``q2_window_one_day_zero_width``, measured on three symbols).
        assert first_second != last_second and last_second - first_second == 86399


def test_yahoo_dated_adapter_refuses_adjclose_at_construction_rather_than_answering_with_close():
    """``field="adjclose"`` is deliberate for two live ingredients and the dated parser reads
    ``close`` only, because a backfilled ``adjclose`` has no point-in-time meaning at all — it
    drifts retroactively with every dividend and split (PID.md, WO-1.16 scope correction). So the
    combination raises where it is written, rather than being resolved quietly into the
    unadjusted close, which would report a different QUANTITY than the live collector stores
    under the same ingredient."""
    with pytest.raises(ValueError):
        _yahoo(field="adjclose", observation_date="2015-06-08")
    # Neither half is refused on its own: adjclose stays available to the LIVE adapter, and a
    # dated request for the close — named or defaulted — is built normally.
    assert _yahoo(field="adjclose")._url().endswith("range=10d&interval=1d")
    assert "period1=" in _yahoo(field="close", observation_date="2015-06-08")._url()
    assert "period1=" in _yahoo(observation_date="2015-06-08")._url()


def test_yahoo_dated_adapter_refuses_a_date_it_cannot_read_at_construction():
    """A string we cannot read as a date is not one we may turn into a window."""
    for unreadable in ("2015-6-8", "06/08/2015", "yesterday", "2015-06-31", ""):
        with pytest.raises(ValueError):
            _yahoo(observation_date=unreadable)


def test_yahoo_dated_adapter_lets_a_400_stay_a_failure_where_fred_turns_its_404_into_empty():
    """THE DELIBERATE ASYMMETRY WITH ``FredAdapter``, pinned as an asymmetry: the two adapters are
    asked the same kind of question in the same test and answer differently, on purpose.

    ``FredAdapter`` NEEDS its carve-out — FRED answers a window on a real gap date with ``404``
    and an HTML page, so without the translation every non-trading day would be a fetch failure.
    Yahoo's gap day is already representable as ``200`` with the bar arrays absent (the EMPTY
    test above), so a 400 here is reachable only by an IMPOSSIBLE window — before the first
    trade, in the future, or reversed — which is the REQUEST being wrong. Translated to EMPTY it
    would be recorded as "the symbol did not print that day" and a driver whose dates ran ahead
    of the clock could log quiet EMPTYs for dates that have not happened."""
    def refused(url, timeout, headers=None):
        raise AdapterFetchError("HTTP_ERROR", 400)  # q4_* / q5_window_reversed, an impossible window

    with pytest.raises(AdapterFetchError) as raised:
        _yahoo(observation_date="1980-01-02", getter=refused).fetch(timeout_seconds=5.0)
    assert raised.value.error_class == "HTTP_ERROR" and raised.value.http_status == 400
    # Not a mode-dependent accident: the undated adapter raises the same way, and so does a 404.
    with pytest.raises(AdapterFetchError):
        _yahoo(getter=refused).fetch(timeout_seconds=5.0)

    def missing(url, timeout, headers=None):
        raise AdapterFetchError("HTTP_ERROR", 404)

    with pytest.raises(AdapterFetchError):
        _yahoo(observation_date="2015-06-08", getter=missing).fetch(timeout_seconds=5.0)

    # FredAdapter, the same 404, the same dated mode: EMPTY, an ANSWER rather than a failure.
    # This is the behaviour being deliberately NOT copied, not an oversight in one of the two.
    fred = A.FredAdapter("T5YIE", None, observation_date="2015-06-20", source_id="fred.T5YIE",
                         as_of_rule="obs_date", unit="percent", clock=lambda: NOW, getter=missing)
    assert fred.fetch(timeout_seconds=5.0).payload == {"unit": "percent"}


def test_multpl_first_row():
    body = "<tr><td>Oct 9, 2026</td><td>\n&#x2002;\n41.87\n</td></tr><tr><td>Sep 1, 2026</td><td>40</td></tr>"
    assert A.parse_multpl_table(body, "ratio") == {"unit": "ratio", "observation_date": "2026-10-09", "value": 41.87}


def test_multpl_unrecognised_page_is_malformed_not_empty():
    assert "unit" not in A.parse_multpl_table("<html>layout changed</html>", "ratio")


# --- as-of ------------------------------------------------------------------------------ #


def test_month_end_rule_and_cap_at_today():
    assert A.as_of_for("2026-08-01", "month_end", NOW).date().isoformat() == "2026-08-31"
    assert A.as_of_for("2026-10-01", "month_end", NOW).date().isoformat() == "2026-10-11"  # never in the future
    assert A.as_of_for("2026-10-08", "obs_date", NOW).date().isoformat() == "2026-10-08"


def test_unknown_as_of_rule_raises():
    with pytest.raises(ValueError):
        A.as_of_for("2026-10-08", "bogus", NOW)


# --- adapters through the core's collect() into the store -------------------------------- #


def _run(store, ing_id, getter):
    ing = next(i for i in INGREDIENTS if i.source_id == ing_id)
    adapter = build_adapter(ing, lambda: NOW)
    adapter._getter = getter
    return collect(adapter, policy=POLICY, sink=store, ledger=store, collector_run_id="t", started_utc=NOW,
                   delay=DelayKind.WALL_CLOCK), ing


@pytest.fixture
def store(tmp_path):
    with SqliteStore(str(tmp_path / "t.sqlite")) as s:
        yield s


def test_ok_fetch_becomes_one_reading_and_refetch_adds_observation_not_reading(store):
    body = "observation_date,DFF\n2026-10-08,3.88\n"
    result, ing = _run(store, "fred.DFF", lambda *a: body)
    assert isinstance(result.final_outcome, OK) and result.reading_admitted
    again, _ = _run(store, "fred.DFF", lambda *a: body)
    assert isinstance(again.final_outcome, OK) and not again.reading_admitted
    assert sum(n for _, _, n in store.outcome_counts()) == 2
    assert store._db.execute("select count(*) from raw_reading").fetchone()[0] == 1


def test_transport_failure_is_recorded_and_makes_no_reading(store):
    def boom(*a):
        raise AdapterFetchError("CONNECTION_FAILED")

    result, _ = _run(store, "fred.DFF", boom)
    assert isinstance(result.final_outcome, FetchFailed)
    assert store.latest_reading("fred.DFF") is None


def test_malformed_body_is_recorded_malformed_never_defaulted(store):
    result, _ = _run(store, "fred.DFF", lambda *a: "observation_date,WRONG\n2026-10-08,1\n")
    assert isinstance(result.final_outcome, Malformed)
    assert store.latest_reading("fred.DFF") is None


def test_store_is_append_only(store):
    _run(store, "fred.DFF", lambda *a: "observation_date,DFF\n2026-10-08,3.88\n")
    for sql in ("UPDATE raw_reading SET payload='{}'", "DELETE FROM raw_reading",
                "UPDATE raw_observation SET outcome='OK'", "DELETE FROM raw_observation"):
        with pytest.raises(Exception, match="append-only"):
            store._db.execute(sql)


# --- WO-1.14: the vintage column, and what an already-written file does with it ----------- #

#: ``raw_reading`` exactly as it stood BEFORE the vintage column — the shape of the live DEV
#: collector's file. Written out in full rather than derived, because a migration test that
#: builds its "old" file from today's schema is testing nothing.
_PRE_VINTAGE_RAW_READING = """
CREATE TABLE raw_reading (
    reading_id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_id TEXT NOT NULL, source_as_of_utc TEXT NOT NULL,
    payload TEXT NOT NULL CHECK (json_type(payload) = 'object'),
    observation_id INTEGER NOT NULL REFERENCES raw_observation(observation_id),
    admitted_utc TEXT NOT NULL,
    UNIQUE (source_id, source_as_of_utc)
);
CREATE TRIGGER raw_reading_no_update BEFORE UPDATE ON raw_reading
    BEGIN SELECT RAISE(ABORT, 'raw_reading is append-only'); END;
CREATE TRIGGER raw_reading_no_delete BEFORE DELETE ON raw_reading
    BEGIN SELECT RAISE(ABORT, 'raw_reading is append-only'); END;
"""


def _pre_vintage_file(path) -> None:
    """A file at the old schema carrying one admitted reading, as the live collector's is."""
    import sqlite3 as _sqlite3

    from ingestion.store import _SCHEMA

    db = _sqlite3.connect(str(path), isolation_level=None)
    before = _SCHEMA.split("CREATE TABLE IF NOT EXISTS raw_reading")[0]
    db.executescript(before + _PRE_VINTAGE_RAW_READING)
    db.execute("INSERT INTO raw_observation (source_id, adapter_id, collector_run_id, attempt_number,"
               " requested_utc, observed_utc, outcome, source_as_of_utc) VALUES"
               " ('fred.DFF','a','r',1,'2026-10-13T00:00:00Z','2026-10-13T00:00:01Z','OK','2026-10-08T00:00:00Z')")
    db.execute("INSERT INTO raw_reading (source_id, source_as_of_utc, payload, observation_id, admitted_utc)"
               " VALUES ('fred.DFF','2026-10-08T00:00:00Z','{\"value\": 3.88}',1,'2026-10-13T00:00:01Z')")
    db.close()


def _reading_columns(path) -> list:
    import sqlite3 as _sqlite3

    db = _sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    try:
        return [row[1] for row in db.execute("PRAGMA table_info(raw_reading)")]
    finally:
        db.close()


def test_the_vintage_check_is_built_from_the_declared_vocabulary_not_retyped():
    from ingestion.store import _VINTAGE_COLUMN
    from ingestion.vintage import VINTAGE_LABELS

    for label in VINTAGE_LABELS:
        assert f"'{label}'" in _VINTAGE_COLUMN
    assert _VINTAGE_COLUMN.count("'") == 2 * len(VINTAGE_LABELS), "a label the vocabulary does not declare"


def test_a_label_that_is_not_a_bare_word_is_refused_rather_than_interpolated():
    """The CHECK cannot be parameterised; the refusal is what stands in for the placeholder."""
    from ingestion.store import _as_sql_literals

    assert _as_sql_literals(("original", "current_only")) == "'original', 'current_only'"
    for bad in ("o'brien", "DROP", "two words", "", "1st"):
        with pytest.raises(ValueError, match="not an admissible vintage label"):
            _as_sql_literals((bad,))


def test_an_existing_file_gains_the_column_and_keeps_every_row(tmp_path):
    """The live DEV collector's file: already written, opened again by a newer store."""
    path = tmp_path / "live.sqlite"
    _pre_vintage_file(path)
    assert "vintage" not in _reading_columns(path)

    with SqliteStore(str(path)) as store:
        rows = store._db.execute("SELECT source_id, payload, vintage FROM raw_reading").fetchall()
    assert rows == [("fred.DFF", '{"value": 3.88}', None)], "a pre-existing reading was lost or guessed at"
    assert _reading_columns(path)[-1] == "vintage"


def test_bringing_an_old_file_forward_is_idempotent_and_leaves_the_same_schema_as_a_new_one(tmp_path):
    migrated, fresh = tmp_path / "old.sqlite", tmp_path / "new.sqlite"
    _pre_vintage_file(migrated)
    for _ in range(3):  # every collector pass re-opens the file; only the first may alter it
        SqliteStore(str(migrated)).close()
    SqliteStore(str(fresh)).close()

    def ddl(path):
        import sqlite3 as _sqlite3

        db = _sqlite3.connect(f"file:{path}?mode=ro", uri=True)
        try:
            return db.execute("SELECT sql FROM sqlite_master WHERE name='raw_reading'").fetchone()[0]
        finally:
            db.close()

    assert _reading_columns(migrated) == _reading_columns(fresh)
    assert "vintage" in ddl(migrated) and "vintage" in ddl(fresh)


def test_the_column_admits_the_two_declared_labels_and_null_and_refuses_anything_else(store):
    from ingestion.vintage import VINTAGE_CURRENT_ONLY, VINTAGE_ORIGINAL

    store._db.execute("INSERT INTO raw_observation (source_id, adapter_id, collector_run_id, attempt_number,"
                      " requested_utc, observed_utc, outcome) VALUES ('s','a','r',1,'t','t','OK')")
    def admit(as_of, vintage):
        store._db.execute("INSERT INTO raw_reading (source_id, source_as_of_utc, payload, observation_id,"
                          " admitted_utc, vintage) VALUES ('s',?,'{}',1,'t',?)", (as_of, vintage))

    admit("1", VINTAGE_ORIGINAL)
    admit("2", VINTAGE_CURRENT_ONLY)
    admit("3", None)  # pre-dates vintage tracking: a third state, not a default
    for bad in ("ORIGINAL", "original ", "backfilled", "revised"):
        with pytest.raises(Exception, match="CHECK constraint failed"):
            admit("4", bad)


def test_the_gui_door_never_migrates_the_file_it_only_reads(tmp_path):
    """A read-only handle must not be the thing that changes a schema, even by accident."""
    path = tmp_path / "live.sqlite"
    _pre_vintage_file(path)
    SqliteStore(str(path), read_only=True).close()
    assert "vintage" not in _reading_columns(path)


def test_http_get_does_not_follow_redirects(monkeypatch):
    import urllib.error

    class Op:
        def open(self, *a, **k):
            raise urllib.error.HTTPError("u", 307, "r", {}, None)

    monkeypatch.setattr(A.urllib.request, "build_opener", lambda *h: Op())
    with pytest.raises(AdapterFetchError) as e:
        A.http_get("https://x", 1)
    assert "https://x" not in str(e.value)  # a stable class only; no URL or exception text


# --- report ----------------------------------------------------------------------------- #


def test_report_never_reads_missing_as_live_and_marks_derived_partial_not_tractable(store):
    states = {s["id"]: s["state"] for s in indicator_states(store, NOW)}
    assert states["vix_level"] == "MISSING"
    assert states["private_credit_stress"] == "MISSING"  # WO-1.8: wired; nothing fetched yet
    assert states["ism_manufacturing"] == "MISSING"
    assert states["sloos_bank_lending"] == "MISSING"  # the manual leg has never been entered: never complete on one leg
    _run(store, "fred.DFF", lambda *a: "observation_date,DFF\n2026-10-08,3.88\n")
    assert {s["id"]: s["state"] for s in indicator_states(store, NOW)}["fed_funds_rate"] == "LIVE"


def test_report_flags_an_old_reading_stale_not_live(store):
    _run(store, "fred.DFF", lambda *a: "observation_date,DFF\n2026-01-08,3.88\n")
    assert {s["id"]: s["state"] for s in indicator_states(store, NOW)}["fed_funds_rate"] == "STALE"


def test_yahoo_drops_a_bar_dated_today_so_a_partial_intraday_bar_is_never_a_close():
    body = '{"chart":{"result":[{"timestamp":[1791244800,1791331200],"indicators":{"quote":[{"close":[10.5,11.5]}]}}]}}'
    out = A.parse_yahoo_chart(body, "usd", 0, today=date(2026, 10, 7))
    assert out["value"] == 10.5 and out["observation_date"] == "2026-10-06"
    assert "value" not in A.parse_yahoo_chart(body, "usd", 0, today=date(2026, 10, 6))


def test_report_flags_a_failing_feed_even_when_the_last_good_reading_is_in_window(store):
    _run(store, "fred.DFF", lambda *a: "observation_date,DFF\n2026-10-08,3.88\n")

    def boom(*a):
        raise AdapterFetchError("x")

    _run(store, "fred.DFF", boom)
    s = {x["id"]: x["state"] for x in indicator_states(store, NOW)}
    assert s["fed_funds_rate"] == "FEED_FAILING"


# --- WO-1.6: legacy-source reuse (gold_spot, buffett_indicator, monetisation_flag) ------------------ #

import json  # noqa: E402

PM = json.dumps([
    {"d": "2026-10-07", "v": [4180.5, 3100.0, 3600.0], "is_cancelled": False},
    {"d": "2026-10-08", "v": [4201.25, 3110.0, 3610.0], "is_cancelled": False},
    {"d": "2026-10-09", "v": [None, None, None], "is_cancelled": False},
])
AM = json.dumps([
    {"d": "2026-10-08", "v": [4195.0, 3105.0, 3605.0], "is_cancelled": False},
    {"d": "2026-10-09", "v": [4216.5, 3120.0, 3620.0], "is_cancelled": False},
])


def test_lbma_prefers_pm_for_a_date_and_falls_back_to_am_only_for_a_date_with_no_pm():
    # 10-09 has no PM fix yet (null) so its AM fix is the newest figure; 10-08 would have used PM (4201.25).
    assert A.parse_lbma_gold(PM, AM, "usd_per_oz") == {"unit": "usd_per_oz", "observation_date": "2026-10-09", "value": 4216.5}
    pm_only_latest = json.dumps([{"d": "2026-10-09", "v": [4220.0, 1, 1]}])
    assert A.parse_lbma_gold(pm_only_latest, AM, "usd_per_oz")["value"] == 4220.0  # PM beats AM for the same date


def test_lbma_skips_cancelled_and_null_rows_but_never_a_non_numeric_figure():
    cancelled = json.dumps([{"d": "2026-10-09", "v": [1.0, 1.0, 1.0], "is_cancelled": True},
                            {"d": "2026-10-08", "v": [4201.25, 1, 1]}])
    assert A.parse_lbma_gold(cancelled, "[]", "u")["observation_date"] == "2026-10-08"
    bad = json.dumps([{"d": "2026-10-09", "v": ["n/a", 1, 1]}])
    out = A.parse_lbma_gold(bad, "[]", "u")
    assert out["value"] == "n/a"  # passed through so the closed schema rejects it: MALFORMED, not skipped


def test_lbma_unrecognised_bodies_are_malformed_and_an_empty_one_is_empty():
    assert "unit" not in A.parse_lbma_gold("<html>Attention Required</html>", AM, "u")
    assert "unit" not in A.parse_lbma_gold(PM, '{"d": 1}', "u")
    assert "unit" not in A.parse_lbma_gold('[{"v": [1]}]', AM, "u")
    assert A.parse_lbma_gold("[]", "[]", "u") == {"unit": "u"}


def test_lbma_adapter_asks_for_both_fixes_with_the_browser_style_agent_and_records_a_403_not_a_value(store):
    # WO-1.12 retarget, NOT a weakening: ``lbma.gold_fix_usd`` (gold_spot) is gone — HERMES serves that row
    # now — but the LBMA adapter is STILL WIRED, as the gold leg of ``gold_real_rate_cross``
    # (``lbma.gold_fix_usd.history``). The same two GETs, the same agent and the same 403 are asserted
    # against that id, so the failing-endpoint evidence this test carries is kept rather than deleted. The
    # indicator it now sinks is gold_real_rate_cross; gold_spot is asserted UNAFFECTED, which is the whole
    # point of giving HERMES a NEW source id.
    seen = []

    def fake(url, timeout, headers):
        seen.append((url, dict(headers or {})))
        return PM if "gold_pm" in url else AM

    result, ing = _run(store, "lbma.gold_fix_usd.history", fake)
    assert [u for u, _ in seen] == [A.LBMA_PM_URL, A.LBMA_AM_URL]
    assert all(h == {"User-Agent": A.LBMA_USER_AGENT} for _, h in seen)
    assert isinstance(result.final_outcome, OK) and result.final_outcome.payload["value"] == 4216.5

    def blocked(url, timeout, headers):
        raise AdapterFetchError("HTTP_ERROR", 403)  # the Cloudflare "Attention Required" refusal seen on 2026-10-11

    refused, _ = _run(store, "lbma.gold_fix_usd.history", blocked)
    assert isinstance(refused.final_outcome, FetchFailed) and refused.final_outcome.http_status == 403
    states = {x["id"]: x["state"] for x in indicator_states(store, NOW)}
    assert states["gold_real_rate_cross"] == "FEED_FAILING"
    assert states["gold_spot"] == "MISSING"  # its own id, never read in this test: NOT dragged down by LBMA


def test_fred_history_carries_raw_levels_oldest_first_and_a_bad_level_is_malformed_not_dropped():
    body = "observation_date,WALCL\n2026-09-23,6747704\n2026-09-30,6743031\n2026-10-07,6747560\n"
    out = A.parse_fred_csv(body, "WALCL", "usd_millions", history=2)
    assert out["observation_date"] == "2026-10-07" and out["value"] == 6747560.0
    assert out["history"] == [["2026-09-30", 6743031.0], ["2026-10-07", 6747560.0]]
    assert "history" not in A.parse_fred_csv(body, "WALCL", "usd_millions")
    junk = "observation_date,WALCL\n2026-09-30,abc\n2026-10-07,6747560\n"
    out = A.parse_fred_csv(junk, "WALCL", "usd_millions", history=2)
    assert out["history"][0] == ["2026-09-30", "abc"]  # a token, rejected by the closed schema downstream


def test_quarter_end_as_of_rule_ages_a_quarter_start_dated_figure_from_the_period_it_describes():
    assert A.as_of_for("2026-04-01", "quarter_end", NOW) == datetime(2026, 6, 30, tzinfo=timezone.utc)
    assert A.as_of_for("2026-01-01", "quarter_end", NOW) == datetime(2026, 3, 31, tzinfo=timezone.utc)
    assert A.as_of_for("2026-10-01", "quarter_end", NOW) == datetime(2026, 10, 11, tzinfo=timezone.utc)  # capped at today


def test_the_three_wo_1_6_indicators_are_served_and_no_longer_listed_not_tractable():
    served = {i for ing in INGREDIENTS for i in ing.serves}
    for ind in ("gold_spot", "buffett_indicator", "monetisation_flag"):
        assert ind in served and ind not in NOT_TRACTABLE
    assert set(NOT_TRACTABLE) == set()  # WO-1.8 wired the last one, as a disclosed proxy


def test_substituted_feeds_are_exactly_the_five_that_differ_from_the_ratified_row_and_say_so():
    feeds = {row["id"]: row["source"]["feed"] for row in MAPPING}
    assert set(SUBSTITUTED_FEEDS) == {"buffett_indicator", "monetisation_flag", "ism_manufacturing", "gold_real_rate_cross",
                                       "private_credit_stress", "sloos_bank_lending"}
    assert "PROVISIONAL" in SUBSTITUTED_FEEDS["gold_real_rate_cross"] and "NOT-OWNER-RATIFIED" in SUBSTITUTED_FEEDS["gold_real_rate_cross"]
    assert "provisional" in SUBSTITUTED_FEEDS["ism_manufacturing"] and "Richmond" in SUBSTITUTED_FEEDS["ism_manufacturing"]
    assert "Wilshire" in feeds["buffett_indicator"] and "Treasury/BEA" in feeds["monetisation_flag"]
    assert "OWNER CONFIRMATION" in SUBSTITUTED_FEEDS["monetisation_flag"]


def test_the_window_overrides_never_exceed_the_engines_relevance_ceiling_and_are_exactly_the_recorded_two():
    from crash_detector.staleness import RELEVANCE_WINDOW_CEILING_SECONDS
    from ingestion.catalog import WINDOW_OVERRIDES, window_seconds

    assert set(WINDOW_OVERRIDES) == {"buffett_indicator", "private_credit_stress"}
    assert window_seconds("private_credit_stress", 10368000) == 7 * 86400 <= RELEVANCE_WINDOW_CEILING_SECONDS
    assert WINDOW_OVERRIDES["private_credit_stress"][1]
    assert window_seconds("buffett_indicator", 3888000) == 120 * 86400 <= RELEVANCE_WINDOW_CEILING_SECONDS
    assert window_seconds("hy_oas", 691200) == 691200.0
    assert WINDOW_OVERRIDES["buffett_indicator"][1]  # a reason is on record


def test_wo_1_6_ingredients_poll_slowly_and_the_fred_history_ones_ask_for_history():
    by_id = {i.source_id: i for i in INGREDIENTS}
    assert by_id["fred.WALCL"].history >= 54 and by_id["fred.CPILFESL"].history >= 4
    assert by_id["fred.NCBEILQ027S"].as_of_rule == by_id["fred.GDP"].as_of_rule == "quarter_end"
    # WO-1.12: gold_spot's DIRECT ingredient is HERMES' candle close, not the LBMA fix. The LBMA
    # ingredient that remains is the gold_real_rate_cross history leg, and it is a COMPONENT.
    assert by_id["hermes.xau_usd.h4_close"].completes == "DIRECT" and by_id["hermes.xau_usd.h4_close"].serves == ("gold_spot",)
    assert "lbma.gold_fix_usd" not in by_id  # retired with its 403; its history leg keeps its own id
    assert by_id["lbma.gold_fix_usd.history"].serves == ("gold_real_rate_cross",)


# --- WO-1.14: the ALFRED vintage adapter ------------------------------------------------- #
#
# ALFRED IS STOOD UP OFFLINE, not mocked at the function that answers. ``_Alfred`` below is a
# model of the endpoint's THREE behaviours the vintage search turns on — a vintage trail that
# begins somewhere (404 beneath it), vintages that exist but carry no row for the observation
# yet, and vintages that carry the figure as it stood then. A fake that only returned bodies
# could not distinguish the second from the first, which is the whole question being asked.

_OBS = "2008-09-01"  # a quarter-start-dated figure, published weeks after the quarter ended


class _Alfred:
    """The endpoint, offline. Records every URL asked and the headers it was asked with."""

    def __init__(self, *, trail_from: str = "1991-07-15", published: str = "2008-10-30",
                 revisions=(("2008-10-30", "1.0"), ("2008-11-20", "1.5"), ("2009-07-31", "2.0")),
                 column: str = "GDP", observation: str = _OBS, answers_vintage=None):
        self.trail_from, self.published, self.revisions = trail_from, published, list(revisions)
        self.column, self.observation = column, observation
        #: when set, every body claims THIS vintage in its header whatever was asked for
        self.answers_vintage = answers_vintage
        self.asked: list[str] = []
        self.headers: list = []

    def vintages_asked(self) -> list[str]:
        from urllib.parse import parse_qs, urlsplit
        return [parse_qs(urlsplit(u).query)["vintage_date"][0] for u in self.asked]

    def __call__(self, url, timeout, headers=None):
        from urllib.parse import parse_qs, urlsplit
        self.asked.append(url)
        self.headers.append(headers)
        asked = parse_qs(urlsplit(url).query)["vintage_date"][0]
        if asked < self.trail_from:
            raise AdapterFetchError("HTTP_ERROR", 404)  # ALFRED has no such vintage of this series
        header = f"observation_date,{self.column}_{(self.answers_vintage or asked).replace('-', '')}"
        if asked < self.published:
            return header + "\n"  # the vintage exists; it had nothing to say about this date
        value = [v for when, v in self.revisions if when <= asked][-1]
        return f"{header}\n{self.observation},{value}\n"


def _vintage_adapter(getter, observation=_OBS, series="GDP", transformation=None):
    return A.AlfredVintageAdapter(
        series=series, transformation=transformation, observation_date=observation,
        source_id="alfred.GDP", as_of_rule="quarter_end", unit="usd_billions",
        clock=lambda: NOW, getter=getter)


def test_the_vintage_chosen_is_the_first_that_published_the_figure_not_the_latest_revision():
    """THE RULE: the earliest vintage in [observation_date, today] that served a value."""
    alfred = _Alfred()
    payload = _vintage_adapter(alfred).fetch(timeout_seconds=30).payload
    assert payload == {"unit": "usd_billions", "observation_date": _OBS,
                       "value": 1.0, "vintage_date": "2008-10-30"}
    # 1.5 and 2.0 are what the SAME observation says in later vintages, and are not chosen.
    assert [v for _, v in alfred.revisions] == ["1.0", "1.5", "2.0"]


# WO-1.17: 2012-02-29 (gap 1,276 days) and 2026-10-11 (gap 6,614) were parameters of this test
# until the first-publication ceiling landed. They are not bisection boundaries any more, they are
# refusals, so they moved to
# ``test_a_first_serving_vintage_too_distant_to_be_a_publication_event_is_refused`` below rather
# than being deleted. What is left here is every gap the ceiling admits, which is what this test
# is about: the bisection pins the serving day exactly.
@pytest.mark.parametrize("published", ["2008-09-01", "2008-09-02", "2008-10-30"])
def test_the_boundary_is_pinned_exactly_the_first_serving_day_and_never_the_day_before(published):
    """Both arms of the bisection's answer: the day it picks served, the day before did not."""
    alfred = _Alfred(published=published, revisions=((published, "7.25"),))
    payload = _vintage_adapter(alfred).fetch(timeout_seconds=30).payload
    assert payload["vintage_date"] == published and payload["value"] == 7.25


def test_no_vintage_that_predates_the_observation_can_be_the_answer_and_the_floor_is_measured():
    """The search window starts AT the observation; the day before it is probed, not assumed."""
    alfred = _Alfred()
    payload = _vintage_adapter(alfred).fetch(timeout_seconds=30).payload
    asked = alfred.vintages_asked()
    assert payload["vintage_date"] >= _OBS
    assert min(asked) == "2008-08-31"  # the floor: probed to VERIFY it carries nothing
    assert [v for v in asked if v < "2008-08-31"] == []
    # 2 ends + a bisection over 6,615 days. Logarithmic, and inside the declared ceiling.
    assert len(asked) <= 2 + 13 and len(asked) <= A.MAX_VINTAGE_PROBES


def test_a_vintage_that_predates_the_observation_yet_already_serves_it_is_refused_not_answered():
    """The premise broke (a projection series?), so the answer would not be the earliest."""
    alfred = _Alfred(published="2008-08-01", revisions=(("2008-08-01", "1.0"),))
    payload = _vintage_adapter(alfred).fetch(timeout_seconds=30).payload
    assert payload == {"malformed": "vintage_floor"}
    assert "value" not in payload  # refused, never approximated to 2008-09-01


# --- WO-1.17: the first-publication CEILING, the mirror of the vintage_floor check above ---- #
#
# The floor asks "did a vintage serve this figure BEFORE the observation existed?". The ceiling
# asks "is the vintage that first served it too LATE to be a publication event?". Both end in a
# MALFORMED refusal and neither reaches the caller under its own name — the closed
# ``response_schema`` rejects both reason strings identically, so ``ingestion.backfill`` records
# the one class MALFORMED. These tests therefore assert the ADAPTER's payload, which is the only
# place the two refusals are still distinguishable.


def test_a_genuine_near_observation_first_publication_is_untouched_by_the_ceiling():
    """NON-REGRESSION, on the real case MAX_FIRST_PUBLICATION_LAG_DAYS was derived against.

    ``evidence/wo114_backfill_proof.json``'s own measurement: ``fred.GDP`` observation 2025-07-01
    was first served by vintage 2025-12-23 — a 175-day gap, which is a real advance estimate and
    the longest genuine publication lag this project has measured. 175 is well under 365 (it is
    48% of it), and the derivation comment on the constant cites this exact pair as the reason the
    threshold is not tighter: at a 180-day threshold this real first publication would have sat 5
    days from refusal.
    """
    alfred = _Alfred(observation="2025-07-01", published="2025-12-23",
                     revisions=(("2025-12-23", "30331.0"), ("2026-03-26", "30353.9")))
    payload = _vintage_adapter(alfred, observation="2025-07-01").fetch(timeout_seconds=30).payload
    assert payload == {"unit": "usd_billions", "observation_date": "2025-07-01",
                       "value": 30331.0, "vintage_date": "2025-12-23"}
    assert (date.fromisoformat("2025-12-23")
            - date.fromisoformat("2025-07-01")).days == 175 <= A.MAX_FIRST_PUBLICATION_LAG_DAYS
    # The later revision is what the SAME observation says today, and is still not chosen.
    assert payload["value"] != 30353.9


def test_a_first_serving_vintage_too_distant_to_be_a_publication_event_is_refused():
    """§7.1's WORKED EXAMPLE, offline: ``fred.NCBEILQ027S``, archive floor 2013-06-06, an
    observation inside episode 2000-02's window.

    The shape that makes this the hard case, and the reason the bisection cannot see it: the
    observation is 1999-12-01, ALFRED's archive for this series begins 2013-06-06, and EVERY
    vintage beneath that floor answers 404. ``probe``'s ``absent_on_404=True`` turns each 404 into
    the same ``_ABSENT`` an existing-but-silent vintage gives, so the search converges on the
    FLOOR and the floor serves the date (the floor vintage's own span starts 1945-10-01 — the
    archive began in 2013, the series did not). The payload would be well-formed, would carry
    ``vintage_date = 2013-06-06``, and ``ingestion.backfill`` would store it as VINTAGE_ORIGINAL:
    a figure restated 13.5 years later, claiming to be what was knowable in 1999.
    """
    alfred = _Alfred(column="NCBEILQ027S", observation="1999-12-01",
                     trail_from="2013-06-06", published="2013-06-06",
                     revisions=(("2013-06-06", "4000.0"),))
    payload = _vintage_adapter(alfred, observation="1999-12-01",
                               series="NCBEILQ027S").fetch(timeout_seconds=30).payload
    # The EXACT refusal, not merely "it did not answer".
    assert payload == {"malformed": "vintage_too_distant"}
    # And specifically NOT the three other ways this fetch could have failed to answer: it is
    # not EMPTY (today's vintage served the date), not an unreadable body, and not the floor.
    assert payload != {"unit": "usd_billions"}
    assert payload["malformed"] not in ("vintage", "header", "series", "vintage_floor")
    # The search really did converge on the archive floor before the ceiling rejected it; the
    # refusal is a judgement on a found answer, not a failure to find one.
    assert "2013-06-06" in alfred.vintages_asked()
    assert (date.fromisoformat("2013-06-06")
            - date.fromisoformat("1999-12-01")).days == 4936 > A.MAX_FIRST_PUBLICATION_LAG_DAYS


@pytest.mark.parametrize("published,gap,refused", [("2009-09-01", 365, False),
                                                   ("2009-09-02", 366, True)])
def test_the_ceiling_is_strictly_greater_than_the_threshold_and_not_off_by_one(published, gap,
                                                                              refused):
    """The cutoff is a hard number, so both sides of it are pinned.

    The check is ``> MAX_FIRST_PUBLICATION_LAG_DAYS``: a gap OF exactly 365 days is admitted, 366
    is refused. Asserted from both directions because an off-by-one here is silent in either —
    too tight and it discards real point-in-time data, too loose and it admits a restatement.
    """
    assert (date.fromisoformat(published) - date.fromisoformat(_OBS)).days == gap
    alfred = _Alfred(published=published, revisions=((published, "7.25"),))
    payload = _vintage_adapter(alfred).fetch(timeout_seconds=30).payload
    if refused:
        assert payload == {"malformed": "vintage_too_distant"}
    else:
        assert payload["vintage_date"] == published and payload["value"] == 7.25


def test_the_floor_refusal_and_the_ceiling_refusal_cannot_both_fire_on_one_fetch():
    """They are mutually exclusive by CONTROL FLOW, not by coincidence of the dates.

    Both conditions are read off the SAME probe — the day before the observation. ``vintage_floor``
    fires when that probe comes back _SERVED and returns immediately, before the bisection runs,
    so the distance check is never reached. ``vintage_too_distant`` is only reachable when that
    probe came back _ABSENT. One probe cannot be both, so no fetch can produce both refusals and
    neither can shadow the other. Pinned here with a series whose trail is ancient (1991) and
    whose floor probe serves: the distance arithmetic has nothing to measure because only two
    probes were ever issued.
    """
    alfred = _Alfred(published="2008-08-01", revisions=(("2008-08-01", "1.0"),))
    payload = _vintage_adapter(alfred).fetch(timeout_seconds=30).payload
    assert payload == {"malformed": "vintage_floor"}
    assert alfred.vintages_asked() == ["2026-10-11", "2008-08-31"]  # ceiling, floor, then out


def test_a_series_whose_vintage_trail_begins_long_after_the_observation_is_refused_not_answered():
    """The two ICE BofA OAS series' situation, and WHAT CHANGED ABOUT IT IN WO-1.17.

    Until the ceiling landed this test asserted the opposite — that the adapter ANSWERS from the
    trail's first vintage (``vintage_date == "2023-10-16"``, ``value == 3.5``). That answer was
    well-formed and satisfied the vintage rule's words literally, and it was exactly the forgery
    §7.1 of the cost estimate traced: the archive's own floor returned as though it were a
    publication event, for ``ingestion.backfill`` to label ``VINTAGE_ORIGINAL``. A figure that no
    vintage carried until 15.1 years after the observation is not what a collector running in 2008
    would have SEEN, which is the only thing ``VINTAGE_ORIGINAL`` claims. So the expectation is
    inverted deliberately, not relaxed.
    """
    alfred = _Alfred(trail_from="2023-10-16", published="2023-10-16",
                     revisions=(("2023-10-16", "3.5"),))
    payload = _vintage_adapter(alfred).fetch(timeout_seconds=30).payload
    assert payload == {"malformed": "vintage_too_distant"}
    assert "value" not in payload and "vintage_date" not in payload


def test_today_s_vintage_carrying_no_value_for_the_date_is_empty_and_never_an_invented_one():
    alfred = _Alfred(published="2027-01-01")  # nothing has ever published this observation
    adapter = _vintage_adapter(alfred)
    payload = adapter.fetch(timeout_seconds=30).payload
    assert payload == {"unit": "usd_billions"} and adapter.is_empty(payload)
    assert alfred.vintages_asked() == ["2026-10-11"]  # one probe; no search over an empty window


def test_a_404_beneath_the_trail_is_an_answer_but_a_404_at_today_s_vintage_is_a_failure():
    def gone(url, timeout, headers=None):
        raise AdapterFetchError("HTTP_ERROR", 404)

    with pytest.raises(AdapterFetchError) as refused:
        _vintage_adapter(gone).fetch(timeout_seconds=30)
    assert refused.value.error_class == "HTTP_ERROR" and refused.value.http_status == 404
    # ...whereas beneath the ceiling the same 404 is read as "no such vintage" and the search
    # completes. WO-1.17: the trail used here is 2008-10-01 rather than the 2023-10-16 the
    # inverted test above now uses, because the point of THIS assertion is the 404-as-ABSENT
    # branch and a 15-year trail would reach it and then be refused for distance, proving
    # nothing about the 404. The trail still begins AFTER the observation, so every probe
    # beneath 2008-10-01 is a real 404 and the search is driven entirely by them.
    completed = _vintage_adapter(_Alfred(trail_from="2008-10-01", published="2008-10-01",
                                         revisions=(("2008-10-01", "3.5"),))
                                 ).fetch(timeout_seconds=30).payload
    assert completed["value"] == 3.5 and completed["vintage_date"] == "2008-10-01"


def test_any_other_transport_failure_is_never_read_as_an_absent_vintage():
    for failure in (AdapterFetchError("TIMEOUT"), AdapterFetchError("HTTP_ERROR", 500),
                    AdapterFetchError("CONNECTION_FAILED")):
        def boom(url, timeout, headers=None, _f=failure):
            raise _f

        with pytest.raises(AdapterFetchError) as raised:
            _vintage_adapter(boom).fetch(timeout_seconds=30)
        assert raised.value.error_class == failure.error_class


def test_a_body_answering_a_different_vintage_than_the_one_asked_is_malformed_and_stops_the_search():
    alfred = _Alfred(answers_vintage="2015-01-01")
    payload = _vintage_adapter(alfred).fetch(timeout_seconds=30).payload
    assert payload == {"malformed": "vintage"}
    assert len(alfred.asked) == 1  # refused on the first answer; not searched around


@pytest.mark.parametrize("body,expected", [
    ("", "header"),
    ("nonsense", "header"),
    ("observation_date,GDP_20261011,extra\n", "header"),
    ("observation_date,OTHER_20261011\n2008-09-01,1.0\n", "series"),
])
def test_an_unreadable_body_is_malformed_never_an_absent_vintage(body, expected):
    payload = _vintage_adapter(lambda *a, **k: body).fetch(timeout_seconds=30).payload
    assert payload == {"malformed": expected}


def test_a_value_that_is_not_a_number_stops_the_search_and_is_passed_to_the_schema_to_reject():
    alfred = _Alfred(revisions=(("2008-10-30", "n/a"),))
    payload = _vintage_adapter(alfred).fetch(timeout_seconds=30).payload
    assert payload["value"] == "n/a"  # carried untouched, exactly as parse_fred_csv does
    assert len(alfred.asked) == 1     # and the bisection did not step over it
    with pytest.raises(SchemaRejection):
        JsonSchemaValidator().validate(payload, A.AlfredVintageAdapter.response_schema)


def test_the_dot_for_no_data_is_an_absent_vintage_not_a_value():
    """FRED writes ``.`` for no data, and a vintage printing one has not published a figure."""
    out = A.parse_alfred_csv("observation_date,GDP_20081030\n2008-09-01,.\n",
                             "GDP", "u", _OBS, "2008-10-30")
    assert out == {"unit": "u"}


def test_the_observation_is_matched_by_date_and_a_clamped_window_cannot_substitute_another_row():
    """ALFRED clamps an out-of-range window instead of refusing it, so 'the only row' is unsafe."""
    body = ("observation_date,GDP_20081030\n1960-01-01,99.0\n1960-04-01,98.0\n")
    assert A.parse_alfred_csv(body, "GDP", "u", _OBS, "2008-10-30") == {"unit": "u"}
    assert A.parse_alfred_csv(body + f"{_OBS},1.0\n", "GDP", "u", _OBS,
                              "2008-10-30")["value"] == 1.0


def test_a_payload_may_not_state_a_value_without_the_vintage_that_produced_it():
    """The point of the schema: a point-in-time value that does not say WHICH vintage is
    indistinguishable from today's value for the same period."""
    schema = A.AlfredVintageAdapter.response_schema
    good = {"unit": "u", "observation_date": _OBS, "value": 1.0, "vintage_date": "2008-10-30"}
    JsonSchemaValidator().validate(good, schema)
    JsonSchemaValidator().validate({"unit": "u"}, schema)  # EMPTY conforms
    for bad in ({k: v for k, v in good.items() if k != "vintage_date"},
                {k: v for k, v in good.items() if k != "observation_date"},
                {**good, "history": [["2008-09-01", 1.0]]},  # a vintage read carries no history
                {**good, "vintage_date": "30/10/2008"}):
        with pytest.raises(SchemaRejection):
            JsonSchemaValidator().validate(bad, schema)


def test_the_whole_search_is_bounded_by_the_timeout_it_was_given_not_each_request():
    alfred = _Alfred()
    with pytest.raises(AdapterFetchError) as raised:
        _vintage_adapter(alfred).fetch(timeout_seconds=0.0)
    assert raised.value.error_class == "TIMEOUT" and alfred.asked == []


def test_the_probe_count_is_capped_and_exhausting_it_is_a_failure_never_a_partial_answer(monkeypatch):
    alfred = _Alfred()
    monkeypatch.setattr(A, "MAX_VINTAGE_PROBES", 3)
    with pytest.raises(AdapterFetchError) as raised:
        _vintage_adapter(alfred).fetch(timeout_seconds=30)
    assert raised.value.error_class == "VINTAGE_SEARCH_EXHAUSTED"
    assert len(alfred.asked) == 3


def test_every_request_goes_to_the_keyless_alfred_door_naming_its_vintage_and_carries_no_credential():
    from urllib.parse import parse_qs, urlsplit

    alfred = _Alfred(column="M2SL_PC1")
    _vintage_adapter(alfred, series="M2SL", transformation="pc1").fetch(timeout_seconds=30)
    for url in alfred.asked:
        parts = urlsplit(url)
        query = parse_qs(parts.query)
        assert parts.hostname == A.ALFRED_HOST and parts.scheme == "https"
        assert query["id"] == ["M2SL"] and query["transformation"] == ["pc1"]
        assert query["cosd"] == [_OBS] and query["coed"] == [_OBS]
        assert len(query["vintage_date"]) == 1
        assert not {"api_key", "key", "token"} & set(query)
    assert set(alfred.headers) == {None}  # FRED's edge resets on an unfamiliar agent
    assert "api.stlouisfed.org" not in "".join(alfred.asked)


def test_a_series_or_transformation_that_is_not_in_the_permitted_shape_is_refused_at_construction():
    for bad in ("GDP&id=OTHER", "GDP ", "", "../x", "GDP#"):
        with pytest.raises(ValueError):
            _vintage_adapter(_Alfred(), series=bad)
    for bad in ("pc1&vintage_date=2026-01-01", "PC1", " "):
        with pytest.raises(ValueError):
            _vintage_adapter(_Alfred(), transformation=bad)
    with pytest.raises(ValueError):
        _vintage_adapter(_Alfred(), observation="not-a-date")


def test_an_observation_date_that_has_not_happened_yet_is_refused_rather_than_searched_for():
    alfred = _Alfred()
    payload = _vintage_adapter(alfred, observation="2027-03-01").fetch(timeout_seconds=30).payload
    assert payload == {"malformed": "observation_date"} and alfred.asked == []


def test_the_vintage_adapter_is_a_structurally_conformant_source_adapter_and_ages_from_the_period():
    from crash_detector.collectors.adapter import missing_adapter_members

    adapter = _vintage_adapter(_Alfred())
    assert missing_adapter_members(adapter) == ()
    fetched = adapter.fetch(timeout_seconds=30)
    # quarter_end on a quarter-start-dated figure, the same rule any other adapter gets.
    assert fetched.source_as_of_utc == datetime(2008, 9, 30, tzinfo=timezone.utc)


def test_the_vintage_adapter_is_not_a_live_ingredient_kind_nor_a_live_egress_host():
    """NOT a "not yet" any more — WO-1.14's wiring round came past this and left it TRUE.

    The vintage adapter is now constructible, through
    ``ingestion.backfill_adapters.build_backfill_adapter`` and only through it. It is still
    not an ingredient ``kind`` the live catalog polls and ``alfred.stlouisfed.org`` is still
    absent from the live egress declaration, because both of those would say the live
    collector reaches it. ``tests/test_wo114.py`` holds the whole boundary; these two lines
    stay here so the live catalog's own test module fails too if it is reopened.
    """
    assert not any(i.kind == "alfred" for i in INGREDIENTS)
    assert A.ALFRED_HOST not in EGRESS_HOSTS
