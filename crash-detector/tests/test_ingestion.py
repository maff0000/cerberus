"""Offline tests for the WO-1.2b ingestion layer (no network, no clock dependence).

Run with the rest of the suite: ``python3 -m pytest`` (pyproject adds ``src`` and ``.``).
"""

from __future__ import annotations

import json
from datetime import date, datetime, timedelta, timezone
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
    serving_ids = lambda ind: {i.source_id for i in INGREDIENTS if ind in i.serves}  # noqa: E731
    # WO-1.20: the gold leg IS the COMEX futures close now, which is what the ratified row's
    # ``market:GC`` names; WO-1.7 wired the LBMA fix instead and that fix is retired. The
    # docstring's "needs GC and DFII10" is literally true here for the first time.
    #
    # ASSERTED BY SOURCE ID AND NOT BY REF, because the ref no longer distinguishes the two rows:
    # ``yahoo.GC=F`` (history-less, copper_gold) and ``yahoo.GC=F.history`` (2600 rows, this row)
    # are TWO catalog rows over ONE symbol, so ``serving`` answers ``"GC=F"`` for either and a
    # ref-level assertion would pass if the wrong one were wired. The ids are the only spelling
    # that says WHICH row, and which row is the whole question: one of them carries no history at
    # all and the derivation refuses a payload without it.
    assert {"GC=F", "DFII10"} <= serving("gold_real_rate_cross")
    assert {"yahoo.GC=F.history", "fred.DFII10.history"} == serving_ids("gold_real_rate_cross")
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
#
# WO-1.20 DELETED FOUR LBMA TESTS FROM THIS SECTION, and the move is a retirement rather than a
# weakening. They tested ``ingestion.adapters.parse_lbma_gold`` (PM-else-AM selection, cancelled
# and null rows, malformed and empty bodies) and ``LbmaGoldAdapter`` (the two GETs, the legacy
# browser-style User-Agent, and the 403 recorded as a failure rather than a value). All of it is
# GONE from the tree: the endpoint answered HTTP 403 to this host from WO-1.6 to WO-1.20 and never
# once delivered a reading, so ``gold_real_rate_cross``'s gold leg became ``yahoo.GC=F.history``
# and the function, the class, the constants and the kind went with the ingredient.
#
# They were DELETED, not skipped or xfailed, on the precedent of WO-1.19's manual-entry tests
# (see ``tests/test_wo17.py``'s sloos section): there is no function left to call, and a skip
# would be a claim that the behaviour still matters and is merely not being measured. The
# endpoint-refusal evidence those tests carried is not lost — it is recorded in the catalog
# comment on ``yahoo.GC=F.history``, in ``SUBSTITUTED_FEEDS["gold_real_rate_cross"]`` and in
# ``deploy/egress-destinations.yaml``'s removal note, which is where a retired feed's history
# belongs. What the new leg's own life is worth asserting is held in ``tests/test_wo17.py``.


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


def test_the_window_overrides_never_exceed_the_engines_relevance_ceiling_and_are_exactly_the_recorded_four():
    from crash_detector.staleness import RELEVANCE_WINDOW_CEILING_SECONDS
    from ingestion.catalog import WINDOW_OVERRIDES, window_seconds

    # WO-1.19 (2026-10-16): buffett_indicator is NO LONGER one of them. Its override existed only to lift the
    # row's 45 declared days to the old 120-day ceiling; the Owner then RATIFIED 210 days on the row itself, so
    # the override had nothing left to replace. Four remain.
    assert set(WINDOW_OVERRIDES) == {"private_credit_stress", "michigan_sentiment", "m2_yoy", "core_pce_yoy"}
    assert window_seconds("private_credit_stress", 10368000) == 7 * 86400 <= RELEVANCE_WINDOW_CEILING_SECONDS
    assert WINDOW_OVERRIDES["private_credit_stress"][1]
    assert window_seconds("hy_oas", 691200) == 691200.0
    for ident, (seconds, reason) in WINDOW_OVERRIDES.items():
        assert seconds <= RELEVANCE_WINDOW_CEILING_SECONDS, ident
        assert reason, ident  # a reason is on record for every one


def test_buffett_indicator_falls_through_to_its_ratified_window_now_that_the_override_is_gone():
    """The ratified figure, not a code-side replacement, is what the engine applies to this row.

    WO-1.19 Owner ratification (Matt, 2026-10-16) on the measured ALFRED release lag in
    evidence/wo119_release_lag_probe.json: the slower wired leg (NCBEILQ027S) lags the quarter END by up to
    101 days, so a healthy reading PEAKS at ~192 days old (one ~91-day quarter cycle plus that lag). 210 days
    is the ratified window, giving that measured worst case ~18 days for release variance.
    """
    from crash_detector.staleness import RELEVANCE_WINDOW_CEILING_SECONDS, RelevanceWindow
    from ingestion.catalog import WINDOW_OVERRIDES, window_seconds

    ratified = {row["id"]: row["staleness_window_seconds"] for row in MAPPING}
    assert ratified["buffett_indicator"] == 210 * 86400 == 18_144_000
    assert "buffett_indicator" not in WINDOW_OVERRIDES
    # Nothing shadows it: window_seconds returns the ratified number unchanged.
    applied = window_seconds("buffett_indicator", ratified["buffett_indicator"])
    assert applied == float(210 * 86400)
    # And it is a window the engine will actually admit - it is AT the ceiling, which it derives FROM this row.
    assert applied == RELEVANCE_WINDOW_CEILING_SECONDS
    assert RelevanceWindow(seconds=applied).covers(applied)
    # The old 120-day pin is really gone, not merely renumbered.
    assert applied > 120 * 86400


def test_sloos_bank_lending_ratified_window_covers_its_measured_peak_age_without_an_override():
    """Both legs are aged from the QUARTER START (as_of_rule 'obs_date'), measured lag 30-42 days.

    The peak age is not the lag: this quarter's reading stays current until the next quarter's print lands,
    one ~91-day cycle plus that print's own lag (up to 42 days) later - a measured peak of ~133 days, which
    the previously ratified 120 days did not cover. 150 days covers it with ~17 days of margin.
    """
    from crash_detector.staleness import RELEVANCE_WINDOW_CEILING_SECONDS, RelevanceWindow
    from ingestion.catalog import WINDOW_OVERRIDES, window_seconds

    ratified = {row["id"]: row["staleness_window_seconds"] for row in MAPPING}
    assert ratified["sloos_bank_lending"] == 150 * 86400 == 12_960_000
    assert "sloos_bank_lending" not in WINDOW_OVERRIDES
    applied = window_seconds("sloos_bank_lending", ratified["sloos_bank_lending"])
    assert applied == float(150 * 86400)
    assert applied > 133 * 86400          # covers the real measured peak age
    assert applied > 120 * 86400          # which the window it replaced did not
    # NOT the ceiling: this row is not the widest the mapping declares, buffett_indicator is.
    assert applied < RELEVANCE_WINDOW_CEILING_SECONDS
    assert RelevanceWindow(seconds=applied).covers(applied)


def test_the_relevance_ceiling_is_still_derived_from_the_widest_window_the_ratified_mapping_declares():
    """The ceiling is not a constant of staleness.py's choosing: it tracks the ratified mapping.

    WO-1.19 moved it (120 -> 210 days) only BECAUSE the mapping's widest declaration moved. This test is the
    one that would fail if a future edit raised the ceiling without a ratified row behind it, or widened a row
    past a ceiling that was left behind.
    """
    from crash_detector.staleness import (
        RELEVANCE_WINDOW_CEILING_SECONDS,
        RELEVANCE_WINDOW_CEILING_SOURCE,
        RelevanceWindow,
    )
    from ingestion.catalog import window_seconds

    windows = {row["id"]: row["staleness_window_seconds"] for row in MAPPING}
    widest = max(windows.values())
    assert widest == RELEVANCE_WINDOW_CEILING_SECONDS == 18_144_000.0
    assert [i for i, w in windows.items() if w == widest] == ["buffett_indicator"]
    # Every ratified row, and every window actually APPLIED, is constructible as a RelevanceWindow.
    for ident, declared in windows.items():
        assert RelevanceWindow(seconds=float(window_seconds(ident, declared))).seconds > 0.0, ident
    # The derivation is stated, dated and attributed where the refusal message will quote it.
    for token in ("18,144,000", "210 days", "buffett_indicator", "WO-1.19", "2026-10-16",
                  "wo119_release_lag_probe.json", "sloos_bank_lending", "150"):
        assert token in RELEVANCE_WINDOW_CEILING_SOURCE, token


# --- WO-1.19 item (4): the three MONTHLY rows whose release lag the ratified 45 days did not fit --------- #
#
# The three windows below are DERIVATIONS from publication schedules that were NOT read off a release
# calendar (there is no network on this path) — the catalog entry for each says so. These tests therefore
# pin the NUMBER THAT WAS ADOPTED and the properties that hold whatever the true lag turns out to be: that
# it is wider than the ratified 45 days, that it is inside the engine's relevance ceiling, and that it is
# NOT that ceiling. They are not evidence that the lag is what the reason text says.

RATIFIED_MONTHLY_WINDOW = 45 * 86400  # 3_888_000: what every monthly row in the ratified mapping declares
WO_1_19_MONTHLY_OVERRIDES = {"michigan_sentiment": 75 * 86400, "m2_yoy": 75 * 86400, "core_pce_yoy": 85 * 86400}


def test_the_three_wo_1_19_monthly_rows_resolve_to_their_widened_windows_inside_the_relevance_ceiling():
    from crash_detector.staleness import RELEVANCE_WINDOW_CEILING_SECONDS
    from ingestion.catalog import WINDOW_OVERRIDES, window_seconds

    ratified = {row["id"]: row["staleness_window_seconds"] for row in MAPPING}
    for ident, expected in WO_1_19_MONTHLY_OVERRIDES.items():
        assert ratified[ident] == RATIFIED_MONTHLY_WINDOW, ident      # the window being REPLACED, from the ratified row
        assert window_seconds(ident, ratified[ident]) == float(expected), ident
        assert expected > RATIFIED_MONTHLY_WINDOW, ident              # every one of the three WIDENS, none narrows
        # Inside the engine's own relevance ceiling, and deliberately not AT it: a window wider than the
        # rhythm needs lets a DEAD feed keep reading current (the failure private_credit_stress undoes).
        assert expected <= RELEVANCE_WINDOW_CEILING_SECONDS, ident
        assert expected < RELEVANCE_WINDOW_CEILING_SECONDS, ident
        assert WINDOW_OVERRIDES[ident][1], ident                      # a reason is on record for each


def test_core_pce_yoy_is_the_widest_of_the_three_because_beas_release_is_the_latest():
    # Not three identical numbers: core PCE lands at the very end of M+1, later than CPI for the same month,
    # which is the whole reason cpi_yoy still fits 45 days and this row does not. 85 > 75 is load-bearing.
    from ingestion.catalog import window_seconds

    assert window_seconds("core_pce_yoy", RATIFIED_MONTHLY_WINDOW) > window_seconds("m2_yoy", RATIFIED_MONTHLY_WINDOW)
    assert window_seconds("m2_yoy", RATIFIED_MONTHLY_WINDOW) == window_seconds("michigan_sentiment", RATIFIED_MONTHLY_WINDOW)


def test_michigan_sentiments_override_records_that_it_is_owed_and_not_a_verified_root_cause_fix():
    # This row's own release-lag arithmetic does NOT explain the STALE symptom Matt observed: the Michigan
    # surveys publish WITHIN the month they describe, so the ratified 45 days already covered the lag. The
    # 75 days clears the symptom and is matched to the other two; the catalog entry must keep saying that it
    # is OWED and reversible, so this does not read later as a diagnosed fix. A silent rewrite fails here.
    from ingestion.catalog import WINDOW_OVERRIDES

    reason = WINDOW_OVERRIDES["michigan_sentiment"][1]
    assert "SYMPTOM" in reason and "OWED" in reason
    assert "does NOT explain" in reason or "DIFFERENT cause" in reason
    assert "45" in reason  # the ratified window it is reversible to


def test_cpi_yoy_and_sahm_rule_were_correctly_left_alone_and_still_resolve_to_the_ratified_forty_five_days():
    # The POINT of this test is that these two were EXAMINED and needed no override, not that nobody touched
    # them: their arithmetic already fits inside 45 days (CPI prints ~12 days after its reference month, the
    # Sahm rule follows the employment report at ~5), so an override here would be an unjustified widening —
    # and a wider window than the rhythm needs is exactly how a DEAD feed keeps reading current. Adding one
    # to either row must fail this test and be argued for on its own evidence.
    from ingestion.catalog import WINDOW_OVERRIDES, window_seconds

    ratified = {row["id"]: row["staleness_window_seconds"] for row in MAPPING}
    cadences = {row["id"]: row["cadence"] for row in MAPPING}
    for ident in ("cpi_yoy", "sahm_rule"):
        assert cadences[ident] == "monthly", ident                    # same cadence and same ratified window
        assert ratified[ident] == RATIFIED_MONTHLY_WINDOW, ident      # as the three rows that WERE widened
        assert ident not in WINDOW_OVERRIDES, ident                   # deliberately NOT overridden
        assert window_seconds(ident, ratified[ident]) == float(RATIFIED_MONTHLY_WINDOW), ident
        # and the resolver really is passing the ratified value through untouched, not coincidentally
        # returning 45 days from somewhere else:
        assert window_seconds(ident, 12345.0) == 12345.0, ident


# --- WO-1.19 item (4), the QUARTERLY half: both rows' windows come from the RELEASE CALENDAR ------------- #
#
# ``ingestion.report.indicator_states`` now resolves these two rows' windows from
# ``ingestion.release_calendar`` instead of from ``window_seconds``, and every number involved is
# UNCHANGED by that: both calendar constants reproduce their ratified figures EXACTLY (210 and 150 days,
# neither row carrying an override), so the dispatch is a TRUE NO-OP on resolved values. That is precisely
# what makes it worth testing twice over, because a no-op has no symptom of its own:
#
#   * the ROUTING is now the only observable thing that changed, so it is asserted directly - the two rows
#     must be resolved WITHOUT ``window_seconds`` being consulted at all, and every OTHER row must still be
#     resolved THROUGH it (the WO-1.16/1.18 "prove the routing, not just the destination" pattern);
#   * the no-op itself is pinned as a NON-REGRESSION, because there are now TWO live code paths to the same
#     two numbers - this one, and ``gui.state.build_state``, which still reads ``window_seconds`` - and
#     nothing but a test stops a future edit to either path from silently moving one and not the other.

RELEASE_CALENDAR_WINDOW_DAYS = {"buffett_indicator": 210.0, "sloos_bank_lending": 150.0}

#: Each row's as-of anchor, which is NOT the same anchor for the two: ``buffett_indicator``'s legs are aged
#: from the QUARTER END (``as_of_rule quarter_end``) and ``sloos_bank_lending``'s from the QUARTER START
#: (``obs_date``). The ages below are measured from these, so a window is being tested against the anchor
#: it is actually derived against - the distinction ``release_calendar`` is explicit that it depends on.
BUFFETT_AS_OF = datetime(2026, 6, 30, tzinfo=timezone.utc)   # 2026-Q2, dated 2026-04-01 by FRED
SLOOS_AS_OF = datetime(2026, 7, 1, tzinfo=timezone.utc)      # the 2026-Q3 SLOOS survey


def _both_quarterly_rows_complete(store):
    """Every leg of both quarterly rows, one period each, dated at that row's own as-of anchor."""
    from test_wiring import _put

    _put(store, "fred.NCBEILQ027S", {"unit": "usd_millions", "observation_date": "2026-04-01", "value": 1.0},
         BUFFETT_AS_OF.isoformat().replace("+00:00", "Z"))
    _put(store, "fred.GDP", {"unit": "usd_billions", "observation_date": "2026-04-01", "value": 2.0},
         BUFFETT_AS_OF.isoformat().replace("+00:00", "Z"))
    for leg in ("fred.DRTSCILM", "fred.DRTSCIS"):
        _put(store, leg, {"unit": "net_percent_tightening", "observation_date": "2026-07-01", "value": 6.0},
             SLOOS_AS_OF.isoformat().replace("+00:00", "Z"))


def test_the_two_quarterly_rows_windows_are_the_release_calendar_constants_themselves_not_copies_of_them():
    """Not ``== 210 days`` alone: == the CONSTANT, so a divergence between the two cannot pass."""
    from ingestion import release_calendar
    from ingestion.report import RELEASE_CALENDAR_WINDOWS

    assert set(RELEASE_CALENDAR_WINDOWS) == {"buffett_indicator", "sloos_bank_lending"}
    # Identical to the module's own constants, to the second, and in the derived direction: the test reads
    # the figure from ``release_calendar``, so a change there that ``report`` did not pick up fails here.
    assert RELEASE_CALENDAR_WINDOWS["buffett_indicator"] == float(release_calendar.BUFFETT_INDICATOR_RELEVANCE_SECONDS)
    assert RELEASE_CALENDAR_WINDOWS["sloos_bank_lending"] == float(release_calendar.SLOOS_BANK_LENDING_RELEVANCE_SECONDS)
    # ...and each is the RATIFIED figure, which is the whole claim that this dispatch changes no number.
    ratified = {row["id"]: row["staleness_window_seconds"] for row in MAPPING}
    for ident, days in RELEASE_CALENDAR_WINDOW_DAYS.items():
        assert RELEASE_CALENDAR_WINDOWS[ident] == days * 86400, ident
        assert RELEASE_CALENDAR_WINDOWS[ident] == float(ratified[ident]), ident
    # The derivation is real arithmetic over the measured lag, not a literal re-typed under a function name.
    assert release_calendar.peak_relevance_seconds(cycle_days=91, worst_lag_days=101, tolerance_days=18) == 210 * 86400
    assert release_calendar.peak_relevance_seconds(cycle_days=91, worst_lag_days=42, tolerance_days=17) == 150 * 86400


def test_report_never_asks_window_seconds_about_the_two_calendar_rows_and_still_asks_it_about_every_other(
        store, monkeypatch):
    """The ROUTING, not the destination: the two numbers are unchanged, so routing is all that moved.

    ``window_seconds`` is replaced by a recorder that EXPLODES if it is ever asked about a release-calendar
    row. A future edit that resolved those two rows through the ratified path again would still produce the
    right number today - the figures agree - and would therefore pass every value-based test in this file
    while quietly undoing the traceability this round exists to add. It fails here instead.
    """
    from ingestion import report
    from ingestion.catalog import window_seconds as real_window_seconds

    asked = []

    def recording_window_seconds(indicator_id, ratified_seconds):
        if indicator_id in report.RELEASE_CALENDAR_WINDOWS:
            raise AssertionError(f"report asked window_seconds about {indicator_id}, a release-calendar row")
        asked.append(indicator_id)
        return real_window_seconds(indicator_id, ratified_seconds)

    monkeypatch.setattr(report, "window_seconds", recording_window_seconds)
    _both_quarterly_rows_complete(store)
    states = {s["id"]: s["state"] for s in report.indicator_states(store, NOW)}

    # Neither calendar row went through it - and both were REACHED, so this is not a vacuous pass: a row
    # skipped entirely (NOT_TRACTABLE) would also never reach ``window_seconds``.
    assert not set(asked) & set(RELEASE_CALENDAR_WINDOW_DAYS)
    for ident in RELEASE_CALENDAR_WINDOW_DAYS:
        assert states[ident] == "DERIVED", ident      # resolved, fresh, and a state was computed for it
    # Every OTHER ratified row still resolves THROUGH ``window_seconds``, by equality over the mapping -
    # so adding a third row to the dispatch dict without a test cannot slip past this.
    assert set(asked) == {row["id"] for row in MAPPING} - set(RELEASE_CALENDAR_WINDOW_DAYS)
    assert len(asked) == len(set(asked)) == 29          # the 31 ratified ids, less the two calendar rows
    for already_covered in ("fed_funds_rate", "gold_spot", "michigan_sentiment"):
        assert already_covered in asked, already_covered   # rows with their own coverage above, still routed


def test_the_calendar_resolved_window_is_what_actually_decides_live_or_stale_for_both_rows(store):
    """The destination too: each row flips at ITS OWN calendar window, from ITS OWN anchor."""
    _both_quarterly_rows_complete(store)

    def state_at(ident, as_of, age_days):
        return {s["id"]: s["state"] for s in indicator_states(store, as_of + timedelta(days=age_days))}[ident]

    # Inside the window the rows are DERIVED (both are all-COMPONENT: the engine owns the quantity),
    # beyond it STALE. The flip sits at the calendar figure and at no other number - in particular not at
    # the 120 days ``buffett_indicator`` was pinned to before this WO, nor the 45 its row once declared.
    assert state_at("buffett_indicator", BUFFETT_AS_OF, 209) == "DERIVED"
    assert state_at("buffett_indicator", BUFFETT_AS_OF, 211) == "STALE"
    assert state_at("buffett_indicator", BUFFETT_AS_OF, 130) == "DERIVED"   # STALE under the retired 120
    assert state_at("sloos_bank_lending", SLOOS_AS_OF, 149) == "DERIVED"
    assert state_at("sloos_bank_lending", SLOOS_AS_OF, 151) == "STALE"
    # The two windows are genuinely DIFFERENT, so neither row is reading the other's figure: at 160 days
    # of age the wider row is still live and the narrower one is not.
    assert state_at("buffett_indicator", BUFFETT_AS_OF, 160) == "DERIVED"
    assert state_at("sloos_bank_lending", SLOOS_AS_OF, 160) == "STALE"


def test_the_release_calendar_path_and_the_ratified_path_cannot_silently_diverge_on_either_row(store, monkeypatch):
    """The NON-REGRESSION. Pre-this-round behaviour and this round's behaviour, compared directly.

    Emptying ``RELEASE_CALENDAR_WINDOWS`` restores EXACTLY the pre-this-round dispatch - every row falls
    through to ``window_seconds`` - so the two code paths can be run over the same store at the same
    instants and compared. They must agree on the resolved window AND on every state it produces, at ages
    on both sides of both boundaries.

    This is not a tautology waiting to rot: ``gui.state.build_state`` still resolves ``window_days`` through
    ``window_seconds`` (the old path) and publishes it to the GUI, while this module now reads the calendar.
    The 210/150 the GUI shows and the 210/150 the report enforces are therefore computed by two different
    routes, and nothing else in the suite would notice if a future edit moved one of them alone.
    """
    from ingestion import report
    from ingestion.catalog import window_seconds

    _both_quarterly_rows_complete(store)
    ratified = {row["id"]: row["staleness_window_seconds"] for row in MAPPING}

    # 1. The resolved WINDOW_DAYS agree exactly, by both routes, for both rows.
    for ident, days in RELEASE_CALENDAR_WINDOW_DAYS.items():
        new_days = report.RELEASE_CALENDAR_WINDOWS[ident] / 86400
        old_days = window_seconds(ident, ratified[ident]) / 86400
        assert new_days == old_days == days, ident
        # the figure ``gui.state`` publishes, computed the way it computes it, is that same number
        assert round(window_seconds(ident, ratified[ident]) / 86400, 2) == days, ident

    # 2. ...and so does every STATE, at ages spanning both windows and both boundaries.
    ages = (0, 1, 100, 149, 151, 160, 209, 211, 400)
    for anchor in (BUFFETT_AS_OF, SLOOS_AS_OF):
        for age_days in ages:
            now = anchor + timedelta(days=age_days)
            new_states = {s["id"]: s["state"] for s in report.indicator_states(store, now)}
            with monkeypatch.context() as old_path:
                old_path.setattr(report, "RELEASE_CALENDAR_WINDOWS", {})    # pre-this-round dispatch
                old_states = {s["id"]: s["state"] for s in report.indicator_states(store, now)}
            # EVERY row, not just the two: this round must not have moved anything else either.
            assert new_states == old_states, (anchor.date().isoformat(), age_days)
            # and the comparison is live - the two rows really do change state across this range, so an
            # agreement here is agreement about something.
            assert new_states["buffett_indicator"] in ("DERIVED", "STALE")
    # The ages chosen do straddle both boundaries rather than all landing on one side.
    assert {state_of for state_of in (
        {s["id"]: s["state"] for s in report.indicator_states(store, BUFFETT_AS_OF + timedelta(days=a))}
        ["buffett_indicator"] for a in ages)} == {"DERIVED", "STALE"}


def test_wo_1_6_ingredients_poll_slowly_and_the_fred_history_ones_ask_for_history():
    by_id = {i.source_id: i for i in INGREDIENTS}
    assert by_id["fred.WALCL"].history >= 54 and by_id["fred.CPILFESL"].history >= 4
    assert by_id["fred.NCBEILQ027S"].as_of_rule == by_id["fred.GDP"].as_of_rule == "quarter_end"
    # WO-1.12: gold_spot's DIRECT ingredient is HERMES' candle close, not the LBMA fix.
    assert by_id["hermes.xau_usd.h4_close"].completes == "DIRECT" and by_id["hermes.xau_usd.h4_close"].serves == ("gold_spot",)
    # WO-1.20: the LAST LBMA row is gone too. WO-1.12 retired ``lbma.gold_fix_usd`` (gold_spot)
    # and left ``lbma.gold_fix_usd.history`` standing as gold_real_rate_cross's gold leg; that
    # leg is now ``yahoo.GC=F.history``, so NO ingredient of kind ``lbma`` exists and the kind is
    # asserted ABSENT WHOLESALE rather than id by id — a re-added row under a third spelling
    # would fail this, where a third ``not in`` would not.
    assert not [i for i in INGREDIENTS if i.kind == "lbma"]
    assert not [sid for sid in by_id if sid.startswith("lbma.")]
    assert by_id["yahoo.GC=F.history"].serves == ("gold_real_rate_cross",)


# --- WO-1.17: the FRED REST vintage adapter ----------------------------------------------- #
#
# WHAT REPLACED WHAT. ``AlfredVintageAdapter`` read ``alfred.stlouisfed.org``'s graph CSV, which
# failed for real from 2026-10-18 (it answered the CURRENT value under a label naming today's
# date whatever vintage was asked for). ``FredVintageAdapter`` reads FRED's documented REST API,
# ``api.stlouisfed.org/fred/series/observations``. The old ``_Alfred`` model, the ``parse_alfred_csv``
# tests and the 404-as-absent tests went with the mechanism they described; what they pinned
# that still applies (the rule, the floor, the ceiling and its boundary, EMPTY, the total deadline,
# the probe cap, the closed schema) is re-pinned below against the new endpoint.
#
# THE BODIES BELOW ARE CAPTURED, NOT INVENTED. Every ``_CAPTURED_*`` constant is a literal JSON body
# taken from a real response of the real API on 2026-10-20 (the key is not in a response, and none
# appears here). Where a test needs a state the real API has not been seen to produce — a first
# vintage that predates its observation, a ``.`` row — it DERIVES it from a capture by editing the
# one field concerned (``_edited``), and says so. No test needs the key or the network.

_REST_TODAY = datetime(2026, 10, 20, 12, 0, tzinfo=timezone.utc)
_FAKE_KEY = "k" * 32  # shaped like a key, worth nothing; the real one is never in this tree

#: ``fred.WALCL``, observation 2015-06-10 (the case the real WO-1.17 backfill failed on), wide window.
_CAPTURED_WALCL_2015_06_10 = (
    '{"realtime_start":"1900-01-01","realtime_end":"2026-10-20","observation_start":"2015-06-10",'
    '"observation_end":"2015-06-10","units":"lin","output_type":1,"file_type":"json",'
    '"order_by":"observation_date","sort_order":"asc","count":1,"offset":0,"limit":100000,'
    '"observations":[{"realtime_start":"2015-06-11","realtime_end":"2026-10-20","date":"2015-06-10",'
    '"value":"4468005"}]}')

#: ``fred.GDP``, observation 2000-01-01: thirteen vintages, the first a genuine BEA advance estimate.
_CAPTURED_GDP_2000_Q1 = (
    '{"realtime_start":"1900-01-01","realtime_end":"2026-10-20","observation_start":"2000-01-01",'
    '"observation_end":"2000-01-01","units":"lin","output_type":1,"file_type":"json",'
    '"order_by":"observation_date","sort_order":"asc","count":13,"offset":0,"limit":100000,'
    '"observations":[{"realtime_start":"2000-04-27","realtime_end":"2000-05-24","date":"2000-01-01","value":"9697.2"},'
    '{"realtime_start":"2000-05-25","realtime_end":"2000-06-28","date":"2000-01-01","value":"9697.6"},'
    '{"realtime_start":"2000-06-29","realtime_end":"2000-07-27","date":"2000-01-01","value":"9707.0"},'
    '{"realtime_start":"2000-07-28","realtime_end":"2001-07-26","date":"2000-01-01","value":"9752.7"},'
    '{"realtime_start":"2001-07-27","realtime_end":"2002-07-30","date":"2000-01-01","value":"9668.7"},'
    '{"realtime_start":"2002-07-31","realtime_end":"2003-12-09","date":"2000-01-01","value":"9649.5"},'
    '{"realtime_start":"2003-12-10","realtime_end":"2009-07-30","date":"2000-01-01","value":"9629.4"},'
    '{"realtime_start":"2009-07-31","realtime_end":"2013-07-30","date":"2000-01-01","value":"9709.5"},'
    '{"realtime_start":"2013-07-31","realtime_end":"2014-07-29","date":"2000-01-01","value":"10036.1"},'
    '{"realtime_start":"2014-07-30","realtime_end":"2017-10-26","date":"2000-01-01","value":"10031.0"},'
    '{"realtime_start":"2017-10-27","realtime_end":"2018-07-26","date":"2000-01-01","value":"10031.031"},'
    '{"realtime_start":"2018-07-27","realtime_end":"2021-07-28","date":"2000-01-01","value":"10002.857"},'
    '{"realtime_start":"2021-07-29","realtime_end":"2026-10-20","date":"2000-01-01","value":"10002.179"}]}')

#: ``fred.WALCL``, observation 2002-12-18 — the series' first observation, which predates its own
#: archive: the earliest vintage FRED holds is 2011-07-07, a restatement 3,123 days later.
_CAPTURED_WALCL_2002_12_18 = (
    '{"realtime_start":"1900-01-01","realtime_end":"2026-10-20","observation_start":"2002-12-18",'
    '"observation_end":"2002-12-18","units":"lin","output_type":1,"file_type":"json",'
    '"order_by":"observation_date","sort_order":"asc","count":2,"offset":0,"limit":100000,'
    '"observations":[{"realtime_start":"2011-07-07","realtime_end":"2013-04-17","date":"2002-12-18","value":"720601"},'
    '{"realtime_start":"2013-04-18","realtime_end":"2026-10-20","date":"2002-12-18","value":"719542"}]}')

#: ``fred.WALCL`` on a Saturday: the series carries no such date at any vintage. ``count`` 0.
_CAPTURED_WALCL_NEVER_PUBLISHED = (
    '{"realtime_start":"1900-01-01","realtime_end":"2026-10-20","observation_start":"2015-06-13",'
    '"observation_end":"2015-06-13","units":"lin","output_type":1,"file_type":"json",'
    '"order_by":"observation_date","sort_order":"asc","count":0,"offset":0,"limit":100000,'
    '"observations":[]}')

#: ``fred.BAMLH0A0HYM2``, observation 2024-12-31: first served the SAME day (admitted by the old
#: mechanism with this value, 2.92) — a same-day publication is neither a floor nor a ceiling case.
_CAPTURED_BAML_2024_12_31 = (
    '{"realtime_start":"1900-01-01","realtime_end":"2026-10-20","observation_start":"2024-12-31",'
    '"observation_end":"2024-12-31","units":"lin","output_type":1,"file_type":"json",'
    '"order_by":"observation_date","sort_order":"asc","count":1,"offset":0,"limit":100000,'
    '"observations":[{"realtime_start":"2024-12-31","realtime_end":"2026-10-20","date":"2024-12-31",'
    '"value":"2.92"}]}')

#: ``fred.CPIAUCSL`` ``units=pc1``, observation 2015-06-01, ONE vintage (2015-07-20) that SERVES it.
_CAPTURED_CPI_PC1_SERVED = (
    '{"realtime_start":"2015-07-20","realtime_end":"2015-07-20","observation_start":"2015-06-01",'
    '"observation_end":"2015-06-01","units":"pc1","output_type":1,"file_type":"json",'
    '"order_by":"observation_date","sort_order":"asc","count":1,"offset":0,"limit":100000,'
    '"observations":[{"realtime_start":"2015-07-20","realtime_end":"2015-07-20","date":"2015-06-01",'
    '"value":"0.18454"}]}')

#: The same request at vintage 2015-06-01, before the figure existed: ``200``, ``count`` 0 — NOT 404.
_CAPTURED_CPI_PC1_ABSENT = (
    '{"realtime_start":"2015-06-01","realtime_end":"2015-06-01","observation_start":"2015-06-01",'
    '"observation_end":"2015-06-01","units":"pc1","output_type":1,"file_type":"json",'
    '"order_by":"observation_date","sort_order":"asc","count":0,"offset":0,"limit":100000,'
    '"observations":[]}')

#: What the server answers a WIDE window with when ``units`` is not ``lin`` (HTTP 400; the body is
#: served here as though it were a 200 to prove it is never read as a vintage).
_CAPTURED_REST_400 = (
    '{"error_code":400,"error_message":"Bad Request.  If output_type is \'1\' and units is not '
    '\'lin\', then realtime_start must equal realtime_end or vintage_dates may set only 1 date."}')


def _edited(body: str, edit) -> str:
    """A captured body with ONE concern changed by ``edit(document)``. Used to DERIVE states."""
    document = json.loads(body)
    edit(document)
    return json.dumps(document)


def _vintage_adapter(getter, observation="2015-06-10", series="WALCL", transformation=None,
                     unit="usd_millions", as_of_rule="obs_date", today=_REST_TODAY,
                     api_key=_FAKE_KEY):
    return A.FredVintageAdapter(
        series=series, transformation=transformation, observation_date=observation,
        api_key=api_key, source_id=f"fred.{series}", as_of_rule=as_of_rule, unit=unit,
        clock=lambda: today, getter=getter)


class _Serves:
    """A getter that answers every request with one literal body and records what was asked."""

    def __init__(self, body: str):
        self.body, self.asked, self.headers = body, [], []

    def __call__(self, url, timeout, headers=None):
        self.asked.append(url)
        self.headers.append(headers)
        return self.body

    def queries(self) -> list:
        from urllib.parse import parse_qs, urlsplit
        return [parse_qs(urlsplit(u).query) for u in self.asked]


class _RestPc1:
    """The transformed-series endpoint, offline: SINGLE-DAY windows, SERVED vs ABSENT.

    Its two answers are the two ``_CAPTURED_CPI_PC1_*`` bodies with the vintage date they echo
    replaced by the one asked — the only field that varies between real probes. Which of the two a
    vintage gets is the model's one decision: served from ``first_serving`` onward, absent before.
    """

    def __init__(self, first_serving: str, observation: str = "2015-06-01"):
        self.first_serving, self.observation = first_serving, observation
        self.asked: list = []

    def vintages_asked(self) -> list:
        from urllib.parse import parse_qs, urlsplit
        return [parse_qs(urlsplit(u).query)["realtime_start"][0] for u in self.asked]

    def __call__(self, url, timeout, headers=None):
        from urllib.parse import parse_qs, urlsplit
        self.asked.append(url)
        query = parse_qs(urlsplit(url).query)
        asked = query["realtime_start"][0]
        assert query["realtime_end"] == [asked], "the server refuses a wide window for units != lin"
        if asked < self.first_serving:  # ABSENT: 200, count 0, echoing the vintage asked
            return _edited(_CAPTURED_CPI_PC1_ABSENT,
                           lambda d: d.update(realtime_start=asked, realtime_end=asked))

        def serve(document):  # SERVED: the captured row, its span moved to the vintage asked
            document.update(realtime_start=asked, realtime_end=asked)
            document["observations"][0].update(realtime_start=asked, realtime_end=asked)
        return _edited(_CAPTURED_CPI_PC1_SERVED, serve)


def _cpi_adapter(getter, observation="2015-06-01"):
    return _vintage_adapter(getter, observation=observation, series="CPIAUCSL",
                            transformation="pc1", unit="percent_yoy", as_of_rule="month_end")


# --- the untransformed path: ONE GET ----------------------------------------------------- #


def test_the_vintage_chosen_is_the_first_that_published_the_figure_not_the_latest_revision():
    """THE RULE, on ``fred.GDP`` 2000-Q1 whose thirteen vintages run 9697.2 .. 10002.179."""
    fake = _Serves(_CAPTURED_GDP_2000_Q1)
    payload = _vintage_adapter(fake, observation="2000-01-01", series="GDP",
                               unit="usd_billions", as_of_rule="quarter_end"
                               ).fetch(timeout_seconds=30).payload
    assert payload == {"unit": "usd_billions", "observation_date": "2000-01-01",
                       "value": 9697.2, "vintage_date": "2000-04-27"}
    assert payload["value"] != 10002.179  # what the SAME observation says today
    assert len(fake.asked) == 1


def test_a_failed_real_backfill_date_now_resolves_to_the_real_first_published_value():
    """``fred.WALCL`` 2015-06-10 failed every attempt of the real run (the CSV fault); the REST
    API's earliest vintage for it is 2015-06-11, value 4,468,005 (USD millions — the catalog's
    own unit for WALCL, so there is no scaling to apply)."""
    payload = _vintage_adapter(_Serves(_CAPTURED_WALCL_2015_06_10)).fetch(
        timeout_seconds=30).payload
    assert payload == {"unit": "usd_millions", "observation_date": "2015-06-10",
                       "value": 4468005.0, "vintage_date": "2015-06-11"}


def test_a_same_day_publication_is_admitted_and_reproduces_the_value_the_old_mechanism_stored():
    """BAMLH0A0HYM2 2024-12-31 was admitted by the CSV mechanism as 2.92, vintage 2024-12-31."""
    payload = _vintage_adapter(_Serves(_CAPTURED_BAML_2024_12_31), observation="2024-12-31",
                               series="BAMLH0A0HYM2", unit="percent").fetch(
        timeout_seconds=30).payload
    assert payload == {"unit": "percent", "observation_date": "2024-12-31",
                       "value": 2.92, "vintage_date": "2024-12-31"}


def test_an_untransformed_row_is_exactly_one_wide_get_to_the_rest_host_carrying_the_key():
    fake = _Serves(_CAPTURED_WALCL_2015_06_10)
    _vintage_adapter(fake).fetch(timeout_seconds=30)
    from urllib.parse import urlsplit
    assert len(fake.asked) == 1
    parts, query = urlsplit(fake.asked[0]), fake.queries()[0]
    assert parts.scheme == "https" and parts.hostname == A.FRED_API_HOST
    assert parts.path == "/fred/series/observations"
    assert query["series_id"] == ["WALCL"] and query["file_type"] == ["json"]
    assert query["realtime_start"] == [A.FRED_REALTIME_FLOOR] == ["1900-01-01"]
    assert query["realtime_end"] == ["2026-10-20"]  # the adapter's own clock, not a global
    assert query["observation_start"] == query["observation_end"] == ["2015-06-10"]
    assert "units" not in query  # the default is lin; only a transformed row names a unit
    assert query["api_key"] == [_FAKE_KEY]
    assert set(fake.headers) == {None}


def test_a_date_the_series_never_carried_at_any_vintage_is_empty_not_an_error():
    adapter = _vintage_adapter(_Serves(_CAPTURED_WALCL_NEVER_PUBLISHED), observation="2015-06-13")
    payload = adapter.fetch(timeout_seconds=30).payload
    assert payload == {"unit": "usd_millions"} and adapter.is_empty(payload)


def test_an_observation_date_that_has_not_happened_yet_is_refused_rather_than_searched_for():
    fake = _Serves(_CAPTURED_WALCL_NEVER_PUBLISHED)
    payload = _vintage_adapter(fake, observation="2027-03-03").fetch(timeout_seconds=30).payload
    assert payload == {"malformed": "observation_date"} and fake.asked == []


def test_a_vintage_the_latest_body_no_longer_carries_is_empty():
    """Today's vintage must still serve it — the old ceiling probe's meaning, kept on the new body."""
    withdrawn = _edited(_CAPTURED_GDP_2000_Q1,
                        lambda d: d["observations"][-1].update(realtime_end="2025-01-01"))
    assert _vintage_adapter(_Serves(withdrawn), observation="2000-01-01", series="GDP",
                            unit="usd_billions").fetch(timeout_seconds=30).payload == {
        "unit": "usd_billions"}
    dot = _edited(_CAPTURED_GDP_2000_Q1, lambda d: d["observations"][-1].update(value="."))
    assert _vintage_adapter(_Serves(dot), observation="2000-01-01", series="GDP",
                            unit="usd_billions").fetch(timeout_seconds=30).payload == {
        "unit": "usd_billions"}


def test_a_vintage_printing_the_dot_for_no_data_has_not_published_a_figure():
    """DERIVED: the first vintage prints ``.``; the first one that carries a number is the answer."""
    body = _edited(_CAPTURED_GDP_2000_Q1,
                   lambda d: d["observations"][0].update(value="."))
    payload = _vintage_adapter(_Serves(body), observation="2000-01-01", series="GDP",
                               unit="usd_billions").fetch(timeout_seconds=30).payload
    assert payload["vintage_date"] == "2000-05-25" and payload["value"] == 9697.6


def test_rows_arriving_out_of_order_are_still_read_earliest_first():
    body = _edited(_CAPTURED_GDP_2000_Q1, lambda d: d["observations"].reverse())
    payload = _vintage_adapter(_Serves(body), observation="2000-01-01", series="GDP",
                               unit="usd_billions").fetch(timeout_seconds=30).payload
    assert payload["vintage_date"] == "2000-04-27"


# --- the floor and the ceiling ----------------------------------------------------------- #


def test_a_vintage_that_predates_the_observation_yet_already_serves_it_is_refused_not_answered():
    """DERIVED: GDP's first vintage moved to the day BEFORE the observation. The premise broke
    (a projection series?), so the answer would not be the earliest the window can hold."""
    body = _edited(_CAPTURED_GDP_2000_Q1,
                   lambda d: d["observations"][0].update(realtime_start="1999-12-31"))
    payload = _vintage_adapter(_Serves(body), observation="2000-01-01", series="GDP",
                               unit="usd_billions").fetch(timeout_seconds=30).payload
    assert payload == {"malformed": "vintage_floor"} and "value" not in payload


def test_a_first_serving_vintage_too_distant_to_be_a_publication_event_is_refused():
    """§7.1, on the real WALCL case: observation 2002-12-18 predates the series' archive, whose
    first vintage is 2011-07-07 — a restatement 3,123 days (8.6 years) after the fact, which
    ``ingestion.backfill`` would otherwise store as ``original``."""
    payload = _vintage_adapter(_Serves(_CAPTURED_WALCL_2002_12_18),
                               observation="2002-12-18").fetch(timeout_seconds=30).payload
    assert payload == {"malformed": "vintage_too_distant"}
    assert (date.fromisoformat("2011-07-07")
            - date.fromisoformat("2002-12-18")).days == 3123 > A.MAX_FIRST_PUBLICATION_LAG_DAYS
    assert payload != {"unit": "usd_millions"}  # not EMPTY: the series DOES carry the date


def test_a_genuine_near_observation_first_publication_is_untouched_by_the_ceiling():
    """NON-REGRESSION on the case MAX_FIRST_PUBLICATION_LAG_DAYS was derived against: ``fred.GDP``
    2025-07-01 first served 2025-12-23, a 175-day genuine advance estimate. DERIVED from the
    captured GDP body with only the dates and value of its first vintage changed."""
    def edit(document):
        document["observation_start"] = document["observation_end"] = "2025-07-01"
        for row in document["observations"]:
            row["date"] = "2025-07-01"
        document["observations"] = [
            {"realtime_start": "2025-12-23", "realtime_end": "2026-03-25",
             "date": "2025-07-01", "value": "30331.0"},
            {"realtime_start": "2026-03-26", "realtime_end": "2026-10-20",
             "date": "2025-07-01", "value": "30353.9"}]
    payload = _vintage_adapter(_Serves(_edited(_CAPTURED_GDP_2000_Q1, edit)),
                               observation="2025-07-01", series="GDP",
                               unit="usd_billions").fetch(timeout_seconds=30).payload
    assert payload == {"unit": "usd_billions", "observation_date": "2025-07-01",
                       "value": 30331.0, "vintage_date": "2025-12-23"}
    assert (date.fromisoformat("2025-12-23")
            - date.fromisoformat("2025-07-01")).days == 175 <= A.MAX_FIRST_PUBLICATION_LAG_DAYS


@pytest.mark.parametrize("first_vintage,gap,refused", [("2000-12-31", 365, False),
                                                       ("2001-01-01", 366, True)])
def test_the_ceiling_is_strictly_greater_than_the_threshold_and_not_off_by_one(first_vintage, gap,
                                                                              refused):
    """A gap OF exactly 365 days is admitted, 366 is refused. Both sides pinned because an
    off-by-one is silent in either direction. DERIVED from the captured GDP body."""
    assert (date.fromisoformat(first_vintage) - date.fromisoformat("2000-01-01")).days == gap
    body = _edited(_CAPTURED_GDP_2000_Q1, lambda d: d["observations"][0].update(
        realtime_start=first_vintage, realtime_end="2026-10-20"))
    body = _edited(body, lambda d: d.update(observations=[d["observations"][0]]))
    payload = _vintage_adapter(_Serves(body), observation="2000-01-01", series="GDP",
                               unit="usd_billions").fetch(timeout_seconds=30).payload
    if refused:
        assert payload == {"malformed": "vintage_too_distant"}
    else:
        assert payload["vintage_date"] == first_vintage


# --- the transformed path: bisection over single-day windows ------------------------------ #


def test_the_transformed_rows_are_exactly_the_three_the_wide_window_cannot_serve():
    """Verified against the REAL catalog, not asserted from the brief: of the 18 revision-prone FRED
    rows, exactly these carry a server-side transformation — and the server refuses each of them a
    wide ``realtime`` range."""
    from ingestion.vintage import requires_original_vintage
    prone = [i for i in INGREDIENTS if i.kind == "fred"
             and requires_original_vintage(i.ref, i.transformation)]
    assert len(prone) == 18
    assert sorted(i.source_id for i in prone if i.transformation) == [
        "fred.CPIAUCSL.pc1", "fred.M2SL.pc1", "fred.PCEPILFE.pc1"]


def test_the_bisection_finds_the_first_serving_vintage_with_single_day_windows_only():
    fake = _RestPc1(first_serving="2015-07-17")
    payload = _cpi_adapter(fake).fetch(timeout_seconds=30).payload
    assert payload == {"unit": "percent_yoy", "observation_date": "2015-06-01",
                       "value": 0.18454, "vintage_date": "2015-07-17"}
    asked = fake.vintages_asked()
    assert asked[0] == "2026-10-20" and asked[1] == "2015-05-31"  # today first, then the floor
    # 2 ends + a bisection over 4,161 days. Logarithmic, and inside the declared cap.
    assert len(asked) <= 2 + 13 and len(asked) <= A.MAX_VINTAGE_PROBES
    assert "2015-07-16" in asked and "2015-07-17" in asked  # both sides of the boundary probed
    from urllib.parse import parse_qs, urlsplit
    for url in fake.asked:
        query = parse_qs(urlsplit(url).query)
        assert query["realtime_start"] == query["realtime_end"]  # never a wide window
        assert query["units"] == ["pc1"] and query["series_id"] == ["CPIAUCSL"]
        assert query["api_key"] == [_FAKE_KEY]


@pytest.mark.parametrize("first_serving", ["2015-06-01", "2015-06-02", "2015-07-17", "2016-05-31"])
def test_the_boundary_is_pinned_exactly_the_first_serving_day_and_never_the_day_before(
        first_serving):
    payload = _cpi_adapter(_RestPc1(first_serving=first_serving)).fetch(timeout_seconds=30).payload
    assert payload["vintage_date"] == first_serving


def test_the_bisection_reads_both_captured_answers_and_treats_a_200_with_no_rows_as_absent():
    """The REST API answers a vintage that did not carry the figure ``200`` with ``count`` 0 —
    there is no 404 for the search to lean on any more."""
    fake = _RestPc1(first_serving="2015-07-17")
    _cpi_adapter(fake).fetch(timeout_seconds=30)
    served = [v for v in fake.vintages_asked() if v >= "2015-07-17"]
    absent = [v for v in fake.vintages_asked() if v < "2015-07-17"]
    assert served and absent


def test_a_transformed_vintage_that_predates_the_observation_yet_serves_it_is_refused():
    fake = _RestPc1(first_serving="2015-05-01")
    assert _cpi_adapter(fake).fetch(timeout_seconds=30).payload == {"malformed": "vintage_floor"}
    assert fake.vintages_asked() == ["2026-10-20", "2015-05-31"]  # ceiling, floor, then out


def test_a_transformed_first_serving_vintage_too_distant_is_refused():
    fake = _RestPc1(first_serving="2017-01-01")
    assert _cpi_adapter(fake).fetch(timeout_seconds=30).payload == {
        "malformed": "vintage_too_distant"}


def test_a_transformed_observation_no_vintage_ever_served_is_empty_after_one_probe():
    fake = _RestPc1(first_serving="2027-01-01")
    adapter = _cpi_adapter(fake)
    payload = adapter.fetch(timeout_seconds=30).payload
    assert payload == {"unit": "percent_yoy"} and adapter.is_empty(payload)
    assert fake.vintages_asked() == ["2026-10-20"]


def test_a_wide_window_answer_for_a_transformed_row_is_never_read_as_a_vintage():
    """The server's own 400 body, served as though it were a 200: ``malformed``, not a value."""
    payload = _cpi_adapter(lambda *a, **k: _CAPTURED_REST_400).fetch(timeout_seconds=30).payload
    assert payload == {"malformed": "body"}


def test_the_probe_count_is_capped_and_exhausting_it_is_a_failure_never_a_partial_answer(
        monkeypatch):
    fake = _RestPc1(first_serving="2015-07-17")
    monkeypatch.setattr(A, "MAX_VINTAGE_PROBES", 3)
    with pytest.raises(AdapterFetchError) as raised:
        _cpi_adapter(fake).fetch(timeout_seconds=30)
    assert raised.value.error_class == "VINTAGE_SEARCH_EXHAUSTED" and len(fake.asked) == 3


# --- unreadable bodies, failures, the deadline ------------------------------------------- #


@pytest.mark.parametrize("body,expected", [
    ("", "body"),
    ("<html>nope</html>", "body"),
    ("[]", "body"),
    ('{"observations": "x"}', "body"),
    (_CAPTURED_REST_400, "body"),
    (_edited(_CAPTURED_WALCL_2015_06_10, lambda d: d.update(realtime_end="2026-10-21")),
     "realtime"),
    (_edited(_CAPTURED_WALCL_2015_06_10, lambda d: d.update(realtime_start="2015-06-17")),
     "realtime"),
    (_edited(_CAPTURED_WALCL_2015_06_10, lambda d: d.update(units="pc1")), "units"),
    (_edited(_CAPTURED_WALCL_2015_06_10, lambda d: d.update(observation_start="2015-06-01")),
     "window"),
    (_edited(_CAPTURED_WALCL_2015_06_10,
             lambda d: d["observations"][0].update(realtime_start="1800-01-01")), "row"),
    (_edited(_CAPTURED_WALCL_2015_06_10,
             lambda d: d["observations"][0].update(value=4468005)), "row"),
    (_edited(_CAPTURED_WALCL_2015_06_10, lambda d: d.update(observations=["x"])), "row"),
])
def test_an_unreadable_or_substituted_body_is_malformed_never_an_empty_or_a_value(body, expected):
    """THE PORT OF THE OLD HEADER CHECK. The CSV fault was a server answering a different question
    than the one asked and saying so only in a header; the REST body echoes its question, so a body
    that answers another one is refused rather than recorded as a point-in-time fact."""
    payload = _vintage_adapter(_Serves(body)).fetch(timeout_seconds=30).payload
    assert payload == {"malformed": expected}


def test_a_value_that_is_not_a_number_is_passed_to_the_schema_to_reject():
    body = _edited(_CAPTURED_WALCL_2015_06_10,
                   lambda d: d["observations"][0].update(value="n/a"))
    payload = _vintage_adapter(_Serves(body)).fetch(timeout_seconds=30).payload
    assert payload["value"] == "n/a"  # carried untouched, exactly as parse_fred_csv does
    with pytest.raises(SchemaRejection):
        JsonSchemaValidator().validate(payload, A.FredVintageAdapter.response_schema)


@pytest.mark.parametrize("failure", [AdapterFetchError("TIMEOUT"),
                                     AdapterFetchError("HTTP_ERROR", 400),
                                     AdapterFetchError("HTTP_ERROR", 404),
                                     AdapterFetchError("HTTP_ERROR", 429),
                                     AdapterFetchError("HTTP_ERROR", 500),
                                     AdapterFetchError("CONNECTION_FAILED")])
@pytest.mark.parametrize("transformed", [False, True])
def test_every_transport_failure_propagates_and_none_is_read_as_an_absent_vintage(failure,
                                                                                 transformed):
    """No 404 carve-out any more: the REST API answers absence with a 200, so a 404 (or a 400
    from a mistyped series id) is a real failure on EVERY probe, on BOTH paths."""
    def boom(url, timeout, headers=None):
        raise failure

    adapter = _cpi_adapter(boom) if transformed else _vintage_adapter(boom)
    with pytest.raises(AdapterFetchError) as raised:
        adapter.fetch(timeout_seconds=30)
    assert raised.value.error_class == failure.error_class
    assert raised.value.http_status == failure.http_status
    leaked = repr(raised.value) + str(raised.value)
    assert _FAKE_KEY not in leaked and "api_key" not in leaked and "stlouisfed" not in leaked


@pytest.mark.parametrize("transformed", [False, True])
def test_the_whole_search_is_bounded_by_the_timeout_it_was_given_not_each_request(transformed):
    fake = _RestPc1("2015-07-17") if transformed else _Serves(_CAPTURED_WALCL_2015_06_10)
    adapter = _cpi_adapter(fake) if transformed else _vintage_adapter(fake)
    with pytest.raises(AdapterFetchError) as raised:
        adapter.fetch(timeout_seconds=0.0)
    assert raised.value.error_class == "TIMEOUT" and fake.asked == []


# --- the credential ---------------------------------------------------------------------- #


def test_the_key_is_a_required_keyword_only_argument_and_is_never_read_from_the_environment():
    import inspect

    parameter = inspect.signature(A.FredVintageAdapter.__init__).parameters["api_key"]
    assert parameter.kind is inspect.Parameter.KEYWORD_ONLY and parameter.default is parameter.empty
    with pytest.raises(TypeError):
        A.FredVintageAdapter("WALCL", None, "2015-06-10", source_id="s", as_of_rule="obs_date",
                             unit="u", clock=lambda: _REST_TODAY)
    source = inspect.getsource(A)
    assert "environ" not in source and "getenv" not in source


@pytest.mark.parametrize("bad", ["", "short", "k" * 15, "k" * 65, "k" * 31 + "\n", "k" * 31 + "&",
                                 "k" * 31 + " ", None, 12345])
def test_a_key_that_is_not_in_the_permitted_shape_is_refused_without_being_echoed(bad):
    with pytest.raises(ValueError) as refused:
        _vintage_adapter(_Serves(""), api_key=bad)
    assert "permitted shape" in str(refused.value)
    if isinstance(bad, str) and bad:
        assert bad not in str(refused.value)


def test_the_key_is_in_the_request_url_and_nowhere_else_the_adapter_exposes():
    fake = _Serves(_CAPTURED_WALCL_2015_06_10)
    adapter = _vintage_adapter(fake)
    payload = adapter.fetch(timeout_seconds=30).payload
    assert _FAKE_KEY in fake.asked[0] and fake.asked[0].count("api_key=") == 1
    # The host-declaring URL carries no credential, so reading an egress host off it is safe.
    from urllib.parse import urlsplit
    assert _FAKE_KEY not in adapter._url() and "api_key" not in adapter._url()
    assert urlsplit(adapter._url()).hostname == A.FRED_API_HOST
    assert _FAKE_KEY not in json.dumps(payload) and _FAKE_KEY not in repr(adapter)


def test_a_series_or_transformation_that_is_not_in_the_permitted_shape_is_refused_at_construction():
    for bad in ("GDP&id=OTHER", "GDP ", "", "../x", "GDP#"):
        with pytest.raises(ValueError):
            _vintage_adapter(_Serves(""), series=bad)
    for bad in ("pc1&units=lin", "PC1", " "):
        with pytest.raises(ValueError):
            _vintage_adapter(_Serves(""), transformation=bad)
    with pytest.raises(ValueError):
        _vintage_adapter(_Serves(""), observation="not-a-date")


# --- shape, schema, and what is gone ------------------------------------------------------ #


def test_a_payload_may_not_state_a_value_without_the_vintage_that_produced_it():
    """The point of the schema: a point-in-time value that does not say WHICH vintage is
    indistinguishable from today's value for the same period."""
    schema = A.FredVintageAdapter.response_schema
    good = {"unit": "u", "observation_date": "2015-06-10", "value": 1.0,
            "vintage_date": "2015-06-11"}
    JsonSchemaValidator().validate(good, schema)
    JsonSchemaValidator().validate({"unit": "u"}, schema)  # EMPTY conforms
    for bad in ({k: v for k, v in good.items() if k != "vintage_date"},
                {k: v for k, v in good.items() if k != "observation_date"},
                {**good, "history": [["2015-06-10", 1.0]]},  # a vintage read carries no history
                {**good, "vintage_date": "11/06/2015"}):
        with pytest.raises(SchemaRejection):
            JsonSchemaValidator().validate(bad, schema)


def test_every_payload_the_adapter_produces_conforms_to_the_closed_schema_or_is_rejected_by_it():
    validator, schema = JsonSchemaValidator(), A.FredVintageAdapter.response_schema
    for body in (_CAPTURED_WALCL_2015_06_10, _CAPTURED_GDP_2000_Q1, _CAPTURED_BAML_2024_12_31,
                 _CAPTURED_WALCL_NEVER_PUBLISHED):
        validator.validate(_vintage_adapter(_Serves(body), observation=json.loads(body)[
            "observation_start"]).fetch(timeout_seconds=30).payload, schema)
    with pytest.raises(SchemaRejection):  # both refusals fail the closed schema identically
        validator.validate({"malformed": "vintage_too_distant"}, schema)


def test_the_vintage_adapter_is_a_structurally_conformant_source_adapter_and_ages_from_the_period():
    from crash_detector.collectors.adapter import missing_adapter_members

    adapter = _vintage_adapter(_Serves(_CAPTURED_GDP_2000_Q1), observation="2000-01-01",
                               series="GDP", unit="usd_billions", as_of_rule="quarter_end")
    assert missing_adapter_members(adapter) == ()
    fetched = adapter.fetch(timeout_seconds=30)
    # quarter_end on a quarter-start-dated figure, the same rule any other adapter gets.
    assert fetched.source_as_of_utc == datetime(2000, 3, 31, tzinfo=timezone.utc)
    assert adapter.adapter_id == "cd.ingest.fred_vintage_rest.v1"


def test_the_graph_csv_mechanism_is_gone_whole_and_not_kept_beside_its_replacement():
    for name in ("AlfredVintageAdapter", "parse_alfred_csv", "ALFRED_HOST", "ALFRED_BASE"):
        assert not hasattr(A, name) and name not in A.__all__


def test_the_vintage_adapter_is_not_a_live_ingredient_kind_nor_a_live_egress_host():
    """It is constructible through ``ingestion.backfill_adapters.build_backfill_adapter`` and only
    through it; the REST host is not in the LIVE collector's egress declaration, because that would
    say ``cd-collectors`` reaches it. ``tests/test_wo114.py`` holds the whole boundary."""
    assert not any(i.kind in ("alfred", "fred_vintage") for i in INGREDIENTS)
    assert A.FRED_API_HOST not in EGRESS_HOSTS
