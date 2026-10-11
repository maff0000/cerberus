"""Offline tests for the WO-1.2b ingestion layer (no network, no clock dependence).

Run with the rest of the suite: ``python3 -m pytest`` (pyproject adds ``src`` and ``.``).
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pytest
import yaml

from crash_detector.collectors import DelayKind, RetryPolicy, collect
from crash_detector.collectors.adapter import AdapterFetchError
from crash_detector.observations import OK, FetchFailed, Malformed
from ingestion import adapters as A
from ingestion.catalog import EGRESS_HOSTS, INGREDIENTS, NOT_TRACTABLE, PARTIAL, build_adapter
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
    assert len(ids) == 30
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
            # every FRED series / CBOE index token an ingredient uses appears in the row's feed
            token = ing.ref if ing.kind in ("fred", "cboe") else None
            if token:
                assert token in feeds[ind], (ing.source_id, ind, feeds[ind])


def test_every_declared_input_of_a_derived_indicator_is_ingested():
    """gold_real_rate_cross needs GC and DFII10; vix_term_structure needs VIX and VIX3M."""
    serving = lambda ind: {i.ref for i in INGREDIENTS if ind in i.serves}  # noqa: E731
    assert {"GC=F", "DFII10"} <= serving("gold_real_rate_cross")
    assert {"VIX", "VIX3M"} <= serving("vix_term_structure")
    assert {"HYG", "LQD"} <= serving("credit_stress_hyg_lqd")
    assert {"RSP", "SPY"} <= serving("breadth_rsp_spy")
    assert {"HG=F", "GC=F"} <= serving("copper_gold")


def test_adapter_urls_reach_only_registered_egress_hosts_and_registry_matches():
    from urllib.parse import urlsplit

    hosts = {urlsplit(build_adapter(i, lambda: NOW)._url()).hostname for i in INGREDIENTS}
    assert hosts == set(EGRESS_HOSTS)
    registry = yaml.safe_load((ROOT / "deploy/egress-destinations.yaml").read_text())["destinations"]
    assert {d["host"] for d in registry} == hosts


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
    assert states["buffett_indicator"] == "NOT_TRACTABLE"
    _run(store, "fred.DFF", lambda *a: "observation_date,DFF\n2026-10-08,3.88\n")
    assert {s["id"]: s["state"] for s in indicator_states(store, NOW)}["fed_funds_rate"] == "LIVE"


def test_report_flags_an_old_reading_stale_not_live(store):
    _run(store, "fred.DFF", lambda *a: "observation_date,DFF\n2026-01-08,3.88\n")
    assert {s["id"]: s["state"] for s in indicator_states(store, NOW)}["fed_funds_rate"] == "STALE"
