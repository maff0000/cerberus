"""WO-1.12: ``gold_spot`` = the close of HERMES' published XAU/USD H4 candle.

NOT a feed substitution. The ratified row's feed is ``market:XAUUSD`` with provenance ``spot``, and HERMES
publishes live OANDA XAU/USD — spot gold, not a futures contract and not a fix. It replaces the LBMA
gold-fix endpoint, which answers HTTP 403 to this host.

What these tests hold down is the REFUSAL discipline, because this is the first ingredient whose publisher
is a system we do not own and whose contract can change under us without warning: a body that is not the
contract this adapter was written against must be MALFORMED and must never be read as if it were.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone

import pytest

from crash_detector.collectors import DelayKind, RetryPolicy, collect
from crash_detector.collectors.adapter import AdapterFetchError
from crash_detector.observations import OK, FetchFailed, Malformed
from ingestion import adapters as A
from ingestion.catalog import INGREDIENTS, NON_HTTP_PEERS, build_adapter
from ingestion.report import indicator_states
from ingestion.store import SqliteStore

NOW = datetime(2026, 10, 13, 12, 0, tzinfo=timezone.utc)
POLICY = RetryPolicy(max_attempts=1, timeout_seconds=5.0, backoff_seconds=0.0)
ING_ID = "hermes.xau_usd.h4_close"
KEY = "hermes:candles:XAU_USD:H4:latest:v1"


def _body(**over) -> str:
    candle = {"instrument": "XAU_USD", "timeframe": "H4", "timestamp_utc": "2026-10-13T00:00:00Z",
              "open": 4200.0, "high": 4225.5, "low": 4198.25, "close": 4216.5, "is_closed": True}
    envelope = {"contract": A.HERMES_CANDLE_CONTRACT, "contract_version": A.HERMES_CANDLE_CONTRACT_VERSION,
                "status": "OK", "data": candle}
    for key, value in over.items():
        (candle if key in candle else envelope)[key] = value
    return json.dumps(envelope)


@pytest.fixture
def store(tmp_path):
    with SqliteStore(str(tmp_path / "t.sqlite")) as s:
        yield s


def _run(store, getter):
    ing = next(i for i in INGREDIENTS if i.source_id == ING_ID)
    adapter = build_adapter(ing, lambda: NOW)
    adapter._getter = getter
    return collect(adapter, policy=POLICY, sink=store, ledger=store, collector_run_id="t", started_utc=NOW,
                   delay=DelayKind.WALL_CLOCK)


# --- the key, and only that key --------------------------------------------------------- #


def test_the_key_is_derived_from_the_adapters_own_instrument_and_timeframe_not_from_a_response():
    assert A.hermes_latest_key("XAU_USD", "H4") == KEY
    seen = []
    ing = next(i for i in INGREDIENTS if i.source_id == ING_ID)
    adapter = build_adapter(ing, lambda: NOW)
    adapter._getter = lambda key, timeout: seen.append(key) or _body()
    adapter.fetch(timeout_seconds=5.0)
    # ONE read, of the one key, and a body claiming a different instrument cannot redirect the next one
    assert seen == [KEY]
    adapter._getter = lambda key, timeout: seen.append(key) or _body(instrument="EUR_USD")
    assert adapter.fetch(timeout_seconds=5.0).payload == {"malformed": "series"}
    assert seen == [KEY, KEY]   # the second read went to the same key


def test_the_peer_is_declared_and_the_adapter_has_no_http_url():
    ing = next(i for i in INGREDIENTS if i.source_id == ING_ID)
    assert ing.kind == "hermes" and ing.serves == ("gold_spot",) and ing.completes == "DIRECT"
    assert f"{A.HERMES_PEER[0]}:{A.HERMES_PEER[1]}/db{A.HERMES_PEER[2]}" in NON_HTTP_PEERS
    # the disclosure travels with the declaration: read-only, and the key is named in it
    assert "read-only" in NON_HTTP_PEERS[f"{A.HERMES_PEER[0]}:{A.HERMES_PEER[1]}/db{A.HERMES_PEER[2]}"]
    assert KEY in NON_HTTP_PEERS[f"{A.HERMES_PEER[0]}:{A.HERMES_PEER[1]}/db{A.HERMES_PEER[2]}"]


# --- the parser: a close, or nothing ----------------------------------------------------- #


def test_a_good_candle_yields_its_close_dated_by_its_own_utc_day():
    out = A.parse_hermes_candle(_body(), "XAU_USD", "H4", "usd_per_oz")
    assert out == {"unit": "usd_per_oz", "observation_date": "2026-10-13", "value": 4216.5}


def test_nothing_but_the_close_is_carried_through():
    out = A.parse_hermes_candle(_body(), "XAU_USD", "H4", "usd_per_oz")
    assert set(out) == {"unit", "observation_date", "value"}  # open/high/low and the geometry are read past


def test_an_absent_key_is_empty_and_never_a_defaulted_price():
    assert A.parse_hermes_candle(None, "XAU_USD", "H4", "usd_per_oz") == {"unit": "usd_per_oz"}


@pytest.mark.parametrize("over, why", [
    ({"status": "DEGRADED"}, "the publisher declines to vouch for it"),
    ({"is_closed": False}, "the bar is still forming"),
])
def test_an_unvouched_or_unclosed_candle_is_empty_not_a_number(over, why):
    assert A.parse_hermes_candle(_body(**over), "XAU_USD", "H4", "usd_per_oz") == {"unit": "usd_per_oz"}, why


@pytest.mark.parametrize("text", [
    "not json at all",
    "[1, 2, 3]",
    '{"contract": "hermes.candles.latest", "contract_version": "v2", "status": "OK", "data": {}}',
    '{"contract": "something.else", "contract_version": "v1", "status": "OK", "data": {}}',
])
def test_a_body_that_is_not_the_contract_we_were_written_against_is_malformed(text):
    assert "unit" not in A.parse_hermes_candle(text, "XAU_USD", "H4", "usd_per_oz")


@pytest.mark.parametrize("over", [{"instrument": "EUR_USD"}, {"timeframe": "H1"}])
def test_a_candle_for_a_different_series_under_the_same_key_is_malformed(over):
    """The key says one thing; if the body says another we are reading a different series by a familiar name."""
    assert A.parse_hermes_candle(_body(**over), "XAU_USD", "H4", "usd_per_oz") == {"malformed": "series"}


@pytest.mark.parametrize("stamp", [None, 1760313600, "not-a-date", "2026-13-45T00:00:00Z"])
def test_an_unreadable_timestamp_is_malformed_never_dated_by_our_own_clock(stamp):
    assert A.parse_hermes_candle(_body(timestamp_utc=stamp), "XAU_USD", "H4", "usd_per_oz") == {"malformed": "date"}


@pytest.mark.parametrize("close", [None, "4216.5", True, float("nan"), float("inf")])
def test_a_close_that_is_not_a_finite_number_is_carried_as_text_for_the_boundary_to_refuse(close):
    out = A.parse_hermes_candle(_body(close=close), "XAU_USD", "H4", "usd_per_oz")
    assert out["value"] == str(close)  # not coerced, not dropped: the schema boundary refuses it


# --- through collect() into the store ---------------------------------------------------- #


def test_a_good_read_admits_the_close_and_gold_spot_reads_live(store):
    result = _run(store, lambda key, timeout: _body())
    assert isinstance(result.final_outcome, OK) and result.final_outcome.payload["value"] == 4216.5
    assert {x["id"]: x["state"] for x in indicator_states(store, NOW)}["gold_spot"] == "LIVE"


def test_a_later_candle_the_same_utc_day_does_not_overwrite_the_first_one_admitted(store):
    """Auditor finding 2 (WO-1.2b): the store keeps the FIRST payload admitted per source period."""
    _run(store, lambda key, timeout: _body())
    _run(store, lambda key, timeout: _body(timestamp_utc="2026-10-13T20:00:00Z", close=4301.0))
    assert store.latest_reading(ING_ID)["payload"]["value"] == 4216.5  # nothing averaged, nothing carried forward


def test_a_malformed_body_is_recorded_as_malformed_and_gold_spot_does_not_read_live(store):
    result = _run(store, lambda key, timeout: _body(contract_version="v99"))
    assert isinstance(result.final_outcome, Malformed)
    assert {x["id"]: x["state"] for x in indicator_states(store, NOW)}["gold_spot"] != "LIVE"


def test_a_stopped_hermes_is_a_failing_feed_or_an_empty_read_never_a_calm_one(store):
    def down(key, timeout):
        raise AdapterFetchError("CONNECTION_FAILED")

    result = _run(store, down)
    assert isinstance(result.final_outcome, FetchFailed)
    assert {x["id"]: x["state"] for x in indicator_states(store, NOW)}["gold_spot"] in ("FEED_FAILING", "MISSING")


def test_the_fetch_error_classes_carry_no_message_or_peer_detail():
    """PBG-SEC-002: a stable class and nothing else — no host, no port, no exception text."""
    import redis

    for raised, expected in ((redis.exceptions.TimeoutError("192.168.11.10 timed out"), "TIMEOUT"),
                             (redis.exceptions.ConnectionError("refused by 192.168.11.10:6379"), "CONNECTION_FAILED"),
                             (OSError("ENETUNREACH 192.168.11.10"), "CONNECTION_FAILED")):
        class _Client:
            def get(self, key):
                raise raised

            def close(self):
                pass

        original = redis.Redis
        redis.Redis = lambda **kw: _Client()
        try:
            with pytest.raises(AdapterFetchError) as caught:
                A.redis_read(KEY, 5.0)
        finally:
            redis.Redis = original
        assert caught.value.args[0] == expected
        assert A.HERMES_PEER[0] not in str(caught.value) and "timed out" not in str(caught.value)
