"""WO-1.17 - a non-data answer is a SERVICE failure, never MALFORMED.

Found 2026-10-21 during WO-1.17's own verification: FRED went into a site-wide maintenance window
and answered every endpoint ``200`` with an HTML "Site Maintenance" page. The adapters could not
read it, so the store recorded the attempts ``MALFORMED`` - the class that means "FRED gave a
well-formed answer and the answer itself failed validation" - and an outage looked like a refusal.

The two fixtures are the REAL bodies FRED served on 2026-10-21 (``fredgraph.csv`` and the REST API),
captured once and never re-fetched: nothing here touches the network.
"""
from __future__ import annotations

import json
from datetime import date, datetime, timezone
from pathlib import Path

import pytest

from crash_detector.collectors import DelayKind, RetryPolicy, collect
from crash_detector.collectors.adapter import AdapterFetchError
from crash_detector.observations import FetchFailed
from ingestion import adapters as A
from ingestion.backfill_calendar import fred_body_dates
from ingestion.catalog import INGREDIENTS, build_adapter
from ingestion.store import SqliteStore

FIXTURES = Path(__file__).parent / "fixtures"
MAINTENANCE_CSV = (FIXTURES / "fred_maintenance_graph_csv.html").read_text()
MAINTENANCE_API = (FIXTURES / "fred_maintenance_api_json.html").read_text()

TODAY = datetime(2026, 10, 21, 12, 0, tzinfo=timezone.utc)
KEY = "k" * 32  # shaped like a key, worth nothing


class _KnownFloor:
    def floor(self, series, timeout_seconds, getter):
        return date(1990, 1, 1)

    def vintages(self, series, timeout_seconds, getter):
        return [date(2015, 7, 17)]


def _serves(body):
    return lambda url, timeout, headers=None: body


def _vintage(getter, transformation=None, floors=None):
    return A.FredVintageAdapter(
        series="WALCL", transformation=transformation, observation_date="2015-06-10", api_key=KEY,
        archive_floors=floors or A.FredArchiveFloors(KEY, clock=lambda: TODAY),
        source_id="fred.WALCL", as_of_rule="obs_date", unit="usd_millions",
        clock=lambda: TODAY, getter=getter)


def _fred_csv(getter, observation_date=None):
    return A.FredAdapter("DFF", None, observation_date=observation_date, source_id="fred.DFF",
                         as_of_rule="obs_date", unit="percent", clock=lambda: TODAY, getter=getter)


def _failed_with(call):
    with pytest.raises(AdapterFetchError) as raised:
        call()
    return raised.value


def test_the_fixtures_are_the_real_maintenance_pages_and_neither_is_data():
    for body in (MAINTENANCE_CSV, MAINTENANCE_API):
        assert "Site Maintenance" in body and body.lstrip().startswith("<!doctype html>")
        with pytest.raises(ValueError):
            json.loads(body)
    assert "k" * 16 not in MAINTENANCE_API and "api_key" not in MAINTENANCE_API  # no secret rides along


def test_the_class_is_not_one_of_the_refusal_or_validation_classes():
    assert A.NON_DATA_RESPONSE == "NON_DATA_RESPONSE"
    assert A.NON_DATA_RESPONSE not in {"MALFORMED", "HTTP_ERROR", "vintage_archive_floor",
                                       "vintage_too_distant", "vintage_floor"}
    assert not issubclass(AdapterFetchError, ValueError)  # never mistaken for the calendar's ValueError


@pytest.mark.parametrize("require, body", [(A.require_json_body, MAINTENANCE_API),
                                           (A.require_csv_body, MAINTENANCE_CSV),
                                           (A.require_csv_body, ""),
                                           (A.require_json_body, "")])
def test_a_body_that_is_not_the_shape_asked_for_is_a_non_data_response(require, body):
    failure = _failed_with(lambda: require(body))
    assert failure.error_class == A.NON_DATA_RESPONSE and failure.http_status is None


def test_a_body_of_the_right_shape_passes_through_untouched_whatever_it_says():
    assert A.require_json_body('{"anything": [1, 2]}') == '{"anything": [1, 2]}'
    wrong_series = "observation_date,SOMETHING_ELSE\n2026-10-08,1\n"
    assert A.require_csv_body(wrong_series) == wrong_series  # the PARSER refuses this one
    assert A.require_csv_body("observation_date\n2015-07-01\n")  # a header with no value column: ditto


def test_the_archive_floor_lookup_fails_as_a_service_not_as_an_unreadable_floor():
    failure = _failed_with(lambda: _vintage(_serves(MAINTENANCE_API)).fetch(timeout_seconds=5.0))
    assert failure.error_class == A.NON_DATA_RESPONSE


@pytest.mark.parametrize("transformation", [None, "pc1"])
def test_the_observation_requests_fail_as_a_service_on_both_paths(transformation):
    adapter = _vintage(_serves(MAINTENANCE_API), transformation=transformation, floors=_KnownFloor())
    assert _failed_with(lambda: adapter.fetch(timeout_seconds=5.0)).error_class == A.NON_DATA_RESPONSE


@pytest.mark.parametrize("observation_date", [None, "2026-10-08"])
def test_the_csv_adapter_fails_as_a_service_dated_and_undated(observation_date):
    adapter = _fred_csv(_serves(MAINTENANCE_CSV), observation_date)
    assert _failed_with(lambda: adapter.fetch(timeout_seconds=5.0)).error_class == A.NON_DATA_RESPONSE


def test_the_calendar_reader_raises_the_service_failure_not_a_value_error():
    failure = _failed_with(lambda: fred_body_dates(MAINTENANCE_CSV, "DTWEXBGS"))
    assert failure.error_class == A.NON_DATA_RESPONSE
    # a real CSV body with the wrong header is still the calendar's ValueError: well-formed, wrong answer
    with pytest.raises(ValueError):
        fred_body_dates("observation_date,OTHER\n2026-10-08,1\n", "DTWEXBGS")


def test_a_well_formed_answer_that_fails_validation_is_still_malformed():
    substituted = _fred_csv(_serves("observation_date,NOT_DFF\n2026-10-08,3.88\n"))
    assert substituted.fetch(timeout_seconds=5.0).payload == {"malformed": "series"}
    wrong_echo = json.dumps({"realtime_start": "1999-01-01", "realtime_end": "1999-01-01",
                             "units": "lin", "observations": []})
    adapter = _vintage(_serves(wrong_echo), floors=_KnownFloor())
    assert "malformed" in adapter.fetch(timeout_seconds=5.0).payload


def test_through_collect_an_outage_is_recorded_fetch_failed_and_admits_nothing(tmp_path):
    ing = next(i for i in INGREDIENTS if i.source_id == "fred.DFF")
    adapter = build_adapter(ing, lambda: TODAY)
    adapter._getter = _serves(MAINTENANCE_CSV)
    with SqliteStore(str(tmp_path / "t.sqlite")) as store:
        result = collect(adapter, policy=RetryPolicy(max_attempts=1, timeout_seconds=5.0,
                                                     backoff_seconds=0.0),
                         sink=store, ledger=store, collector_run_id="t", started_utc=TODAY,
                         delay=DelayKind.WALL_CLOCK)
        assert isinstance(result.final_outcome, FetchFailed)
        assert result.final_outcome.error_class == A.NON_DATA_RESPONSE
        assert store._db.execute("select outcome, error_class from raw_observation").fetchall() == [
            ("FETCH_FAILED", A.NON_DATA_RESPONSE)]
        assert store._db.execute("select count(*) from raw_reading").fetchone()[0] == 0
