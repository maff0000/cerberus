"""WO-1.17 Fault 4 - the transformed path SCANS the real vintage dates; it does not bisect.

The fixture is REAL FRED (``fred.PCEPILFE`` ``units=pc1``, observation 2000-10-01, captured
2026-10-22): the figure is first served by vintage 2000-11-30 (1.69443) and is ``.`` AGAIN at
2004-01-02 and 2004-01-04, before 2004-01-05 serves a different value. A bisection assumes "serves a
value" never goes true-then-false as the vintage advances; it hit those gaps, converged on 2004-01-05
and refused a genuine first publication as ``vintage_too_distant``. Nothing here touches the network.
"""
from __future__ import annotations

import json
from datetime import date, datetime, timezone
from pathlib import Path
from urllib.parse import parse_qs

import pytest

from crash_detector.collectors.adapter import AdapterFetchError
from ingestion import adapters as A

FIXTURE = json.loads((Path(__file__).parent / "fixtures"
                      / "fred_pcepilfe_pc1_gap_2000_10_01.json").read_text())
TODAY = datetime(2026, 10, 22, 12, 0, tzinfo=timezone.utc)
KEY = "k" * 32


def _key(path, query):
    q = dict(query)
    if path.endswith("/vintagedates"):
        return ("vintagedates", q["limit"])
    return ("observations", q["realtime_start"])


BODIES = {_key(r["path"], r["query"]): r["body"]
          for r in FIXTURE["responses"] + FIXTURE["gap_responses"]}


class _Archive:
    """The captured responses, served by what was asked. Anything NOT captured fails the test, so
    the probes the scan makes are exactly the probes the fixture proves."""

    def __init__(self, overrides=None, fallback_absent=False):
        self.asked, self.overrides, self.fallback_absent = [], overrides or {}, fallback_absent

    def __call__(self, url, timeout, headers=None):
        from urllib.parse import urlsplit
        parts = urlsplit(url)
        query = {k: v[0] for k, v in parse_qs(parts.query).items()}
        key = _key(parts.path, query.items())
        self.asked.append(key)
        if key in self.overrides:
            return self.overrides[key]
        if key not in BODIES and self.fallback_absent and key[0] == "observations":
            document = json.loads(BODIES[("observations", "2004-01-02")])  # a real absent answer
            document["realtime_start"] = document["realtime_end"] = key[1]
            for row in document["observations"]:
                row["realtime_start"] = row["realtime_end"] = key[1]
            return json.dumps(document)
        assert key in BODIES, f"probe not in the captured fixture: {key}"
        return BODIES[key]

    def observation_probes(self):
        return [v for kind, v in self.asked if kind == "observations"]


def _adapter(getter, floors=None):
    return A.FredVintageAdapter(
        series="PCEPILFE", transformation="pc1", observation_date="2000-10-01", api_key=KEY,
        archive_floors=floors or A.FredArchiveFloors(KEY, clock=lambda: TODAY.astimezone(timezone.utc)),
        source_id="fred.PCEPILFE.pc1", as_of_rule="month_end", unit="percent_yoy",
        clock=lambda: TODAY, getter=getter)


def _served(vintage):
    body = json.loads(BODIES[("observations", vintage)])["observations"]
    return body[0]["value"] != "."


def test_the_captured_archive_really_is_not_monotone():
    """The property that broke the bisection, in the real bodies: served, then absent, then served."""
    assert _served("2000-11-30") is True
    assert _served("2004-01-02") is False and _served("2004-01-04") is False
    assert _served("2004-01-05") is True and _served("2026-10-22") is True


def test_the_scan_admits_the_first_publication_the_bisection_wrongly_refused():
    archive = _Archive()
    payload = _adapter(archive).fetch(timeout_seconds=60).payload
    assert payload == {"unit": "percent_yoy", "observation_date": "2000-10-01",
                       "value": 1.69443, "vintage_date": "2000-11-30"}
    # today (served: not EMPTY), the day before the observation (absent: not a vintage_floor), then the
    # archive's own vintage dates in order until one serves. Four observation GETs.
    assert archive.observation_probes() == ["2026-10-22", "2000-09-30", "2000-10-30", "2000-11-30"]
    assert ("observations", "2004-01-02") not in archive.asked  # the gap is never reached


def test_the_vintage_list_costs_one_get_per_series_for_all_the_dates_asked():
    floors = A.FredArchiveFloors(KEY, clock=lambda: TODAY)
    first, second = _Archive(), _Archive()
    _adapter(first, floors).fetch(timeout_seconds=60)
    _adapter(second, floors).fetch(timeout_seconds=60)
    assert first.asked.count(("vintagedates", "10000")) == 1
    assert ("vintagedates", "10000") not in second.asked and ("vintagedates", "1") not in second.asked


def test_the_real_vintage_list_is_ascending_unique_and_starts_at_the_floor():
    listed = A.parse_fred_vintagedates_all(BODIES[("vintagedates", "10000")], realtime_end="2026-10-22")
    assert listed[0] == date(2000, 8, 1)
    assert listed == sorted(set(listed)) and date(2000, 11, 30) in listed


@pytest.mark.parametrize("edit", [
    lambda d: d.update(count=d["count"] + 1),             # truncated: a scan would skip vintages
    lambda d: d.update(vintage_dates=list(reversed(d["vintage_dates"]))),
    lambda d: d.update(realtime_end="2026-10-21"),         # answered another question
    lambda d: d.update(sort_order="desc"),
    lambda d: d.update(vintage_dates=[]),
    lambda d: d.update(vintage_dates=["not-a-date"] + d["vintage_dates"][1:]),
])
def test_a_vintage_list_that_cannot_be_trusted_is_unreadable_never_a_shorter_scan(edit):
    document = json.loads(BODIES[("vintagedates", "10000")])
    edit(document)
    assert A.parse_fred_vintagedates_all(json.dumps(document), realtime_end="2026-10-22") is None


def test_an_unreadable_vintage_list_answers_nothing_and_asks_no_observation():
    archive = _Archive({("vintagedates", "10000"): "[]"})
    payload = _adapter(archive).fetch(timeout_seconds=60).payload
    assert payload == {"malformed": "vintage_list_unreadable"}
    assert archive.observation_probes() == []


def test_a_maintenance_page_for_the_vintage_list_is_a_service_failure():
    page = (Path(__file__).parent / "fixtures" / "fred_maintenance_api_json.html").read_text()
    with pytest.raises(AdapterFetchError) as raised:
        _adapter(_Archive({("vintagedates", "10000"): page})).fetch(timeout_seconds=60)
    assert raised.value.error_class == A.NON_DATA_RESPONSE


def test_a_figure_first_served_only_after_the_window_is_still_too_distant():
    """The ceiling is unchanged: the scan stops at observation + 365 days. Every vintage in the window
    is made absent (a real absent answer, re-dated), so the first served one lies past it."""
    overrides = {}
    for vintage in ("2000-10-30", "2000-11-30"):
        document = json.loads(BODIES[("observations", "2004-01-02")])
        document["realtime_start"] = document["realtime_end"] = vintage
        for row in document["observations"]:
            row["realtime_start"] = row["realtime_end"] = vintage
        overrides[("observations", vintage)] = json.dumps(document)
    archive = _Archive(overrides, fallback_absent=True)
    payload = _adapter(archive).fetch(timeout_seconds=60).payload
    assert payload == {"malformed": "vintage_too_distant"}
    assert max(archive.observation_probes()[2:]) <= "2001-10-01"  # never past the 365-day window
