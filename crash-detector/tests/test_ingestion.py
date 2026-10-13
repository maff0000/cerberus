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
    assert {"DRTSCILM", "sloos_table2_q14"} <= serving("sloos_bank_lending")
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


def test_cboe_date_and_column():
    body = "DATE,OPEN,CLOSE\n10/08/2026,1,2\n10/09/2026,3,14.84\n"
    assert A.parse_cboe_csv(body, "CLOSE", "index") == {"unit": "index", "observation_date": "2026-10-09", "value": 14.84}


def test_cboe_missing_column_is_malformed():
    assert "unit" not in A.parse_cboe_csv("DATE,X\n10/09/2026,1\n", "CLOSE", "index")


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


# --- WO-1.6: legacy-source reuse (gold_spot, buffett_indicator, fiscal_dominance) ------------------ #

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
    for ind in ("gold_spot", "buffett_indicator", "fiscal_dominance"):
        assert ind in served and ind not in NOT_TRACTABLE
    assert set(NOT_TRACTABLE) == set()  # WO-1.8 wired the last one, as a disclosed proxy


def test_substituted_feeds_are_exactly_the_five_that_differ_from_the_ratified_row_and_say_so():
    feeds = {row["id"]: row["source"]["feed"] for row in MAPPING}
    assert set(SUBSTITUTED_FEEDS) == {"buffett_indicator", "fiscal_dominance", "ism_manufacturing", "gold_real_rate_cross",
                                       "private_credit_stress", "sloos_bank_lending"}
    assert "PROVISIONAL" in SUBSTITUTED_FEEDS["gold_real_rate_cross"] and "NOT-OWNER-RATIFIED" in SUBSTITUTED_FEEDS["gold_real_rate_cross"]
    assert "provisional" in SUBSTITUTED_FEEDS["ism_manufacturing"] and "Richmond" in SUBSTITUTED_FEEDS["ism_manufacturing"]
    assert "Wilshire" in feeds["buffett_indicator"] and "Treasury/BEA" in feeds["fiscal_dominance"]
    assert "OWNER CONFIRMATION" in SUBSTITUTED_FEEDS["fiscal_dominance"]


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
