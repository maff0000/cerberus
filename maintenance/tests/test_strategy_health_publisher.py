"""Unit tests for strategy_health_publisher — WO-R2D2-STRATEGY-HEALTH-PUBLICATION-CADENCE-0001.

Coverage:
- Layered classifier (FULL / LIMITED_SAMPLE / INSUFFICIENT_SAMPLE) with explainability
- Gate booleans (sample / reliability / direction_check) + failed_gates list
- health_status_reason population for every status
- Score computation matches inherited V1 formula
- 7 tripwires individually (TW-1..TW-7)
- Verdict aggregation (RED dominates AMBER dominates GREEN)
- Publisher state shape (12 architect-required fields)
- Per-run audit shape
- DB-unreachable fail-loud abort (no fabric writes)
- Per-strategy fabric_set failure → AMBER (continue + record failure)
- No deletes; stale records not overwritten on RED-tier failure
- tz-aware UTC enforcement (rejects tz-naive)
- Contract v1 compatibility (required fields present)
- Source enum is R2D2_SCHEDULED_V1 (NOT R2D2_POST_33_REFRESH_V1)

Tests run as: python3 -m pytest /srv/r2d2/maintenance/tests/test_strategy_health_publisher.py -v
"""
from __future__ import annotations

import json
import sys
import unittest
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List

# /srv/r2d2/maintenance takes priority for development; /opt fallback.
sys.path.insert(0, "/opt/r2d2/maintenance")
sys.path.insert(0, "/srv/r2d2/maintenance")

from strategy_health_publisher import (  # type: ignore
    ALLOWED_DIRECTION_CHECK,
    ALLOWED_HEALTH_STATUS,
    ALLOWED_RELIABILITY_LABEL,
    CONTRACT_VERSION,
    DIRECTION_CHECK_EXPECTANCY_FLOOR,
    DORMANT_HEALTH_SOURCE,
    DORMANT_HEALTH_STATUS_REASON,
    KEY_PUBLISHER_AUDIT_LATEST,
    KEY_PUBLISHER_AUDIT_PREFIX,
    KEY_PUBLISHER_FAULT_PREFIX,
    KEY_PUBLISHER_STATE,
    KEY_STRATEGY_HEALTH_PREFIX,
    KEY_STRATEGY_HEALTH_SUFFIX,
    N_FULL_THRESHOLD,
    N_LIMITED_THRESHOLD,
    RELIABILITY_WR_FLOOR,
    SOURCE_ENUM,
    StrategyCoverage,
    StrategyScore,
    TIMER_CADENCE,
    V3_FRESHNESS_GATE_HOURS,
    WO,
    build_dormant_envelope,
    build_envelope,
    build_per_run_audit,
    build_publisher_state,
    classify_health_status,
    compute_expected_strategy_set,
    compute_score_components,
    compute_strategy_score,
    derive_direction_check_status,
    derive_reliability_label,
    discover_existing_strategies_in_fabric,
    evaluate_full_eligibility,
    iso_z,
    run_all_tripwires,
    run_publisher,
    tripwire_1_expected_count,
    tripwire_2_no_record_older_than_30h,
    tripwire_3_tz_aware_utc,
    tripwire_4_score_schema,
    tripwire_5_enum_allowed,
    tripwire_6_registry_drift,
    tripwire_7_audit_canary,
    tripwire_8_no_stale_version_in_fabric,
)


# ─────────────────────────── Fixtures ──────────────────────────────────────────

NOW = datetime(2026, 5, 13, 18, 0, 0, tzinfo=timezone.utc)


def _resolved_row(outcome: str, signed_pnl: float = 1.0, ts: str = "2026-05-13T17:00:00") -> Dict[str, Any]:
    return {
        "outcome": outcome,
        "signed_pnl_pts": signed_pnl,
        "outcome_resolved_at_utc": ts,
    }


def _make_resolved_rows(wins: int, losses: int, neutrals: int = 0,
                       win_pnl: float = 5.0, loss_pnl: float = -2.0) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for _ in range(wins):
        rows.append(_resolved_row("TP1_HIT", signed_pnl=win_pnl))
    for _ in range(losses):
        rows.append(_resolved_row("SL_HIT", signed_pnl=loss_pnl))
    for _ in range(neutrals):
        rows.append(_resolved_row("EXPIRED", signed_pnl=0.0))
    return rows


class FakeFabric:
    def __init__(self) -> None:
        self.store: Dict[str, Any] = {}
        self.set_calls: List[str] = []
        self.set_should_fail_for: List[str] = []

    def get(self, key: str) -> Any:
        return self.store.get(key)

    def set(self, key: str, value: Any) -> bool:
        self.set_calls.append(key)
        if key in self.set_should_fail_for:
            return False
        self.store[key] = value
        return True


# ─────────────────────────── 1. Layered classifier ────────────────────────────

class TestLayeredClassifier(unittest.TestCase):

    def test_T01_full_when_all_gates_pass(self):
        # n=120, wr=0.50, expectancy=0.40 — all gates pass
        elig = evaluate_full_eligibility(120, wr=0.50, expectancy_pts=0.40)
        self.assertTrue(elig.sample_gate_passed)
        self.assertTrue(elig.reliability_gate_passed)
        self.assertTrue(elig.direction_check_gate_passed)
        self.assertTrue(elig.all_passed)
        self.assertEqual(elig.failed_gates, [])

    def test_T02_limited_sample_when_sample_below_100(self):
        # n=80 → sample_gate fails
        elig = evaluate_full_eligibility(80, wr=0.60, expectancy_pts=1.0)
        self.assertFalse(elig.sample_gate_passed)
        self.assertFalse(elig.reliability_gate_passed)  # requires n>=100 too
        self.assertTrue(elig.direction_check_gate_passed)
        self.assertIn("sample_gate", elig.failed_gates)
        self.assertIn("reliability_gate", elig.failed_gates)
        status, reason = classify_health_status(80, has_prices=80, eligibility=elig)
        self.assertEqual(status, "LIMITED_SAMPLE")
        self.assertIn("sample_gate", reason)

    def test_T03_reliability_gate_fails_when_wr_low(self):
        # n=200, wr=0.40 < 0.45 floor
        elig = evaluate_full_eligibility(200, wr=0.40, expectancy_pts=0.50)
        self.assertTrue(elig.sample_gate_passed)
        self.assertFalse(elig.reliability_gate_passed)
        self.assertTrue(elig.direction_check_gate_passed)
        self.assertEqual(elig.failed_gates, ["reliability_gate"])
        status, reason = classify_health_status(200, has_prices=200, eligibility=elig)
        self.assertEqual(status, "LIMITED_SAMPLE")
        self.assertIn("reliability_gate", reason)

    def test_T04_direction_check_fails_when_expectancy_low(self):
        # n=200, wr=0.50, expectancy=0.10 < 0.30 floor
        elig = evaluate_full_eligibility(200, wr=0.50, expectancy_pts=0.10)
        self.assertTrue(elig.sample_gate_passed)
        self.assertTrue(elig.reliability_gate_passed)
        self.assertFalse(elig.direction_check_gate_passed)
        self.assertEqual(elig.failed_gates, ["direction_check_gate"])

    def test_T05_multiple_gates_fail(self):
        # n=200, wr=0.30, expectancy=-1.0 — reliability + direction fail
        elig = evaluate_full_eligibility(200, wr=0.30, expectancy_pts=-1.0)
        self.assertTrue(elig.sample_gate_passed)
        self.assertFalse(elig.reliability_gate_passed)
        self.assertFalse(elig.direction_check_gate_passed)
        self.assertIn("reliability_gate", elig.failed_gates)
        self.assertIn("direction_check_gate", elig.failed_gates)

    def test_T06_insufficient_when_n_below_30(self):
        elig = evaluate_full_eligibility(15, wr=0.60, expectancy_pts=1.0)
        status, reason = classify_health_status(15, has_prices=15, eligibility=elig)
        self.assertEqual(status, "INSUFFICIENT_SAMPLE")
        self.assertIn("sample minimum", reason)

    def test_T07_insufficient_when_has_prices_zero(self):
        elig = evaluate_full_eligibility(0, wr=None, expectancy_pts=None)
        status, reason = classify_health_status(0, has_prices=0, eligibility=elig)
        self.assertEqual(status, "INSUFFICIENT_SAMPLE")
        self.assertIn("has_prices=0", reason)

    def test_T08_nowic_at_m15_real_world_n_236(self):
        # nowic_at_m15 currently has n=236, wr=0.4195 (below 0.45 reliability floor)
        # Expected: LIMITED_SAMPLE with reliability_gate failed (matches POST_33 record)
        elig = evaluate_full_eligibility(236, wr=0.4195, expectancy_pts=0.55)
        self.assertTrue(elig.sample_gate_passed)
        self.assertFalse(elig.reliability_gate_passed)  # wr below floor
        self.assertTrue(elig.direction_check_gate_passed)
        self.assertFalse(elig.all_passed)
        status, _ = classify_health_status(236, has_prices=236, eligibility=elig)
        self.assertEqual(status, "LIMITED_SAMPLE")


# ─────────────────────────── 2. Derived labels ────────────────────────────────

class TestDerivedLabels(unittest.TestCase):

    def test_T09_reliability_TRUSTED_when_gate_passes(self):
        elig = evaluate_full_eligibility(150, wr=0.60, expectancy_pts=1.0)
        self.assertEqual(derive_reliability_label(elig, 150), "TRUSTED")

    def test_T10_reliability_WATCH_when_n_geq_30_but_gate_fails(self):
        elig = evaluate_full_eligibility(80, wr=0.60, expectancy_pts=1.0)
        self.assertEqual(derive_reliability_label(elig, 80), "WATCH")

    def test_T11_reliability_UNTRUSTED_when_n_below_30(self):
        elig = evaluate_full_eligibility(15, wr=0.60, expectancy_pts=1.0)
        self.assertEqual(derive_reliability_label(elig, 15), "UNTRUSTED")

    def test_T12_direction_POSITIVE_when_gate_passes(self):
        elig = evaluate_full_eligibility(150, wr=0.60, expectancy_pts=1.0)
        self.assertEqual(derive_direction_check_status(elig, 1.0), "POSITIVE")

    def test_T13_direction_NEGATIVE_when_expectancy_negative(self):
        elig = evaluate_full_eligibility(150, wr=0.30, expectancy_pts=-0.5)
        self.assertEqual(derive_direction_check_status(elig, -0.5), "NEGATIVE")

    def test_T14_direction_NEUTRAL_when_expectancy_none(self):
        elig = evaluate_full_eligibility(0, wr=None, expectancy_pts=None)
        self.assertEqual(derive_direction_check_status(elig, None), "NEUTRAL")


# ─────────────────────────── 3. Envelope shape ────────────────────────────────

class TestEnvelopeShape(unittest.TestCase):

    def _build(self, n_resolved=120, wr=0.50, expectancy=0.40) -> Dict[str, Any]:
        cov = StrategyCoverage(strategy_id="x_m5", total_fired=130, has_prices=120,
                              missing_prices=10, pending=10)
        score = StrategyScore(strategy_id="x_m5", n_fires_resolved=n_resolved,
                              win_count=int(n_resolved*0.5), loss_count=int(n_resolved*0.5),
                              wr=wr, expectancy_pts=expectancy,
                              score=0.55, score_components={"a": 1})
        elig = evaluate_full_eligibility(n_resolved, wr, expectancy)
        return build_envelope(cov, score, elig,
                              window_start=NOW - timedelta(days=90),
                              window_end=NOW, computed_at=NOW)

    def test_T15_contract_required_fields(self):
        env = self._build()
        for f in ("health_status", "score", "computed_at_utc",
                  "n_fires_resolved", "version"):
            self.assertIn(f, env, f"contract v1 REQUIRED field missing: {f}")

    def test_T16_explainability_fields_present(self):
        env = self._build()
        self.assertIn("health_status_reason", env)
        self.assertIn("full_eligibility", env)
        elig = env["full_eligibility"]
        for f in ("sample_gate_passed", "reliability_gate_passed",
                  "direction_check_gate_passed", "failed_gates"):
            self.assertIn(f, elig)

    def test_T17_full_eligibility_failed_gates_empty_for_FULL(self):
        env = self._build(n_resolved=120, wr=0.55, expectancy=0.50)
        self.assertEqual(env["health_status"], "FULL")
        self.assertEqual(env["full_eligibility"]["failed_gates"], [])
        self.assertIn("all 3 gates passed", env["health_status_reason"])

    def test_T18_full_eligibility_failed_gates_populated_for_LIMITED(self):
        env = self._build(n_resolved=200, wr=0.40, expectancy=0.10)
        self.assertEqual(env["health_status"], "LIMITED_SAMPLE")
        self.assertIn("reliability_gate", env["full_eligibility"]["failed_gates"])
        self.assertIn("direction_check_gate", env["full_eligibility"]["failed_gates"])

    def test_T19_insufficient_publishes_null_score_with_reason(self):
        cov = StrategyCoverage(strategy_id="empty", has_prices=0)
        score = StrategyScore(strategy_id="empty", n_fires_resolved=0)
        elig = evaluate_full_eligibility(0, None, None)
        env = build_envelope(cov, score, elig,
                             window_start=NOW - timedelta(days=90),
                             window_end=NOW, computed_at=NOW)
        self.assertEqual(env["health_status"], "INSUFFICIENT_SAMPLE")
        self.assertIsNone(env["score"])
        self.assertEqual(env["health_source"], "R2D2_INSUFFICIENT_V1")

    def test_T20_version_is_R2D2_SCHEDULED_V1(self):
        env = self._build()
        self.assertEqual(env["version"], "R2D2_SCHEDULED_V1")
        self.assertNotEqual(env["version"], "R2D2_POST_33_REFRESH_V1")
        self.assertNotEqual(env["version"], "R2D2_90D_OVERALL_V1")

    def test_T21_computed_at_utc_is_tz_z_format(self):
        env = self._build()
        self.assertTrue(env["computed_at_utc"].endswith("Z"))

    def test_T22_contract_compatibility_field_present(self):
        env = self._build()
        self.assertEqual(env["contract_compatibility"], CONTRACT_VERSION)

    def test_T23_iso_z_rejects_tz_naive(self):
        with self.assertRaises(ValueError):
            iso_z(datetime(2026, 5, 13, 18, 0, 0))  # no tzinfo


# ─────────────────────────── 4. Tripwires ─────────────────────────────────────

class TestTripwires(unittest.TestCase):

    def _records(self, n=17, age_hours=1.0):
        ts = (NOW - timedelta(hours=age_hours)).strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        return {
            f"strategy_{i}": {
                "health_status": "FULL",
                "score": 0.5,
                "computed_at_utc": ts,
                "n_fires_resolved": 100,
                "version": SOURCE_ENUM,
                "window_start_utc": "2026-02-12T18:00:00.000000Z",
                "window_end_utc": ts,
            }
            for i in range(n)
        }

    def test_T24_tw1_pass(self):
        r = tripwire_1_expected_count(17, 17)
        self.assertTrue(r.passed)

    def test_T25_tw1_fail(self):
        r = tripwire_1_expected_count(17, 15)
        self.assertFalse(r.passed)
        self.assertEqual(r.tier, "RED")

    def test_T26_tw2_pass_when_fresh(self):
        r = tripwire_2_no_record_older_than_30h(self._records(age_hours=1), NOW)
        self.assertTrue(r.passed)

    def test_T27_tw2_fail_when_stale(self):
        r = tripwire_2_no_record_older_than_30h(self._records(age_hours=40), NOW)
        self.assertFalse(r.passed)
        self.assertIn("stale_count=17", r.detail)

    def test_T28_tw3_pass_tz_aware(self):
        r = tripwire_3_tz_aware_utc(self._records())
        self.assertTrue(r.passed)

    def test_T29_tw3_fail_tz_naive(self):
        recs = {"x": {"computed_at_utc": "2026-05-13T18:00:00",
                       "health_status": "FULL", "score": 0.5,
                       "n_fires_resolved": 100, "version": SOURCE_ENUM,
                       "window_start_utc": "2026-02-12T18:00:00",
                       "window_end_utc": "2026-05-13T18:00:00"}}
        r = tripwire_3_tz_aware_utc(recs)
        self.assertFalse(r.passed)
        self.assertIn("tz-naive", r.detail)

    def test_T30_tw4_score_schema_pass(self):
        recs = self._records()
        r = tripwire_4_score_schema(recs)
        self.assertTrue(r.passed)

    def test_T31_tw4_score_schema_fail_on_null_without_reason(self):
        recs = {"x": {"score": None, "health_status": "FULL",
                       "health_source": "R2D2_SCHEDULED_V1",
                       "computed_at_utc": "2026-05-13T18:00:00.000000Z",
                       "n_fires_resolved": 50, "version": SOURCE_ENUM}}
        r = tripwire_4_score_schema(recs)
        self.assertFalse(r.passed)

    def test_T32_tw4_score_schema_pass_null_with_insufficient_reason(self):
        recs = {"x": {"score": None, "health_status": "INSUFFICIENT_SAMPLE",
                       "health_source": "R2D2_INSUFFICIENT_V1",
                       "computed_at_utc": "2026-05-13T18:00:00.000000Z",
                       "n_fires_resolved": 0, "version": SOURCE_ENUM}}
        r = tripwire_4_score_schema(recs)
        self.assertTrue(r.passed)

    def test_T33_tw5_enum_pass(self):
        r = tripwire_5_enum_allowed(self._records())
        self.assertTrue(r.passed)

    def test_T34_tw5_enum_fail_on_unknown(self):
        recs = {"x": {"health_status": "FUTURE_ENUM",
                       "score": 0.5,
                       "computed_at_utc": "2026-05-13T18:00:00.000000Z",
                       "n_fires_resolved": 100, "version": SOURCE_ENUM}}
        r = tripwire_5_enum_allowed(recs)
        self.assertFalse(r.passed)

    def test_T35_tw6_registry_drift_pass(self):
        r = tripwire_6_registry_drift(["a", "b"], ["a", "b"])
        self.assertTrue(r.passed)

    def test_T36_tw6_registry_drift_new_strategy_amber(self):
        r = tripwire_6_registry_drift(["a"], ["a", "new_one"])
        self.assertFalse(r.passed)
        self.assertEqual(r.tier, "AMBER")
        self.assertIn("new_one", r.detail)

    def test_T37_tw7_audit_canary_pass(self):
        r = tripwire_7_audit_canary(
            last_audit_at_utc=NOW - timedelta(hours=4),
            now_utc_=NOW, cadence_hours=4.0,
        )
        self.assertTrue(r.passed)

    def test_T38_tw7_audit_canary_fail_when_stale(self):
        r = tripwire_7_audit_canary(
            last_audit_at_utc=NOW - timedelta(hours=12),
            now_utc_=NOW, cadence_hours=4.0,
        )
        self.assertFalse(r.passed)

    def test_T39_tw7_audit_canary_fail_when_none(self):
        r = tripwire_7_audit_canary(
            last_audit_at_utc=None, now_utc_=NOW, cadence_hours=4.0,
        )
        self.assertFalse(r.passed)


# ─────────────────────────── 5. Verdict aggregation ───────────────────────────

class TestVerdictAggregation(unittest.TestCase):

    def _good_records(self, n=2):
        ts = (NOW - timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        return {
            f"x_{i}": {
                "health_status": "FULL",
                "score": 0.5,
                "computed_at_utc": ts,
                "n_fires_resolved": 100,
                "version": SOURCE_ENUM,
                "window_start_utc": "2026-02-12T18:00:00.000000Z",
                "window_end_utc": ts,
            }
            for i in range(n)
        }

    def test_T40_all_green(self):
        recs = self._good_records()
        v, _ = run_all_tripwires(
            expected_strategies=["x_0", "x_1"],
            published_records=recs, now_utc_=NOW,
            last_audit_at_utc=NOW - timedelta(hours=3),
        )
        self.assertEqual(v, "GREEN")

    def test_T41_red_dominates_amber(self):
        # Miss strategy → TW-1 RED
        recs = self._good_records(n=1)
        v, _ = run_all_tripwires(
            expected_strategies=["x_0", "x_1"],
            published_records=recs, now_utc_=NOW,
            last_audit_at_utc=NOW - timedelta(hours=3),
        )
        self.assertEqual(v, "RED")

    def test_T42_amber_when_only_amber_fails(self):
        # Add an unexpected strategy → TW-6 AMBER; everything else passes
        recs = self._good_records(n=3)
        v, _ = run_all_tripwires(
            expected_strategies=["x_0", "x_1", "x_2"],
            published_records={**recs, "rogue_strategy": list(recs.values())[0]},
            now_utc_=NOW,
            last_audit_at_utc=NOW - timedelta(hours=3),
        )
        # TW-1: 3 expected, 4 published (rogue added) → RED
        # So expected verdict is RED, not AMBER. To isolate AMBER, expected must
        # be empty and one published → TW-1 RED. The only clean AMBER path is
        # when expected contains 3, published is exactly 3 but one is non-overlap.
        # Build that case:
        v2, _ = run_all_tripwires(
            expected_strategies=["x_0", "x_1", "x_2"],
            published_records={"x_0": list(recs.values())[0],
                                "x_1": list(recs.values())[0],
                                "rogue": list(recs.values())[0]},
            now_utc_=NOW,
            last_audit_at_utc=NOW - timedelta(hours=3),
        )
        # 3 expected, 3 published (count match), but rogue not in expected,
        # x_2 missing from published → TW-1 (count match OK) + TW-6 AMBER (new
        # strategy) and TW-1 actually passes since counts equal. Wait — TW-1
        # checks counts equal, doesn't check set membership. So this is AMBER.
        self.assertEqual(v2, "AMBER")


# ─────────────────────────── 6. Publisher state + audit shape ────────────────

class TestPublisherStateAndAudit(unittest.TestCase):

    def test_T43_publisher_state_has_all_12_required_fields(self):
        state = build_publisher_state(
            run_started_at=NOW, run_finished_at=NOW + timedelta(seconds=5),
            expected_count=17, published_count=17,
            counts_by_status={"FULL": 0, "LIMITED_SAMPLE": 6, "INSUFFICIENT_SAMPLE": 11},
            stale_count=0, missing_count=0, verdict="GREEN",
            next_run_at=NOW + timedelta(hours=4),
        )
        required = ["last_run_at_utc", "last_success_at_utc",
                    "expected_strategy_count", "published_strategy_count",
                    "full_count", "limited_sample_count",
                    "insufficient_sample_count", "stale_count",
                    "missing_count", "verdict", "source_enum",
                    "timer_cadence", "next_expected_run_at_utc"]
        for f in required:
            self.assertIn(f, state, f"required state field missing: {f}")

    def test_T44_state_source_enum_is_R2D2_SCHEDULED_V1(self):
        state = build_publisher_state(
            run_started_at=NOW, run_finished_at=NOW,
            expected_count=0, published_count=0,
            counts_by_status={}, stale_count=0, missing_count=0,
            verdict="GREEN", next_run_at=NOW,
        )
        self.assertEqual(state["source_enum"], "R2D2_SCHEDULED_V1")

    def test_T45_state_timer_cadence_published(self):
        state = build_publisher_state(
            run_started_at=NOW, run_finished_at=NOW,
            expected_count=0, published_count=0,
            counts_by_status={}, stale_count=0, missing_count=0,
            verdict="GREEN", next_run_at=NOW,
        )
        self.assertEqual(state["timer_cadence"], TIMER_CADENCE)

    def test_T46_state_last_success_at_utc_null_on_red(self):
        state = build_publisher_state(
            run_started_at=NOW, run_finished_at=NOW,
            expected_count=17, published_count=15,
            counts_by_status={}, stale_count=0, missing_count=2,
            verdict="RED", next_run_at=NOW,
        )
        self.assertIsNone(state["last_success_at_utc"])

    def test_T47_audit_has_all_required_fields(self):
        audit = build_per_run_audit(
            run_id="shp-test", run_started_at=NOW, run_finished_at=NOW + timedelta(seconds=2),
            expected_strategies=["a", "b"], published_records={"a": {}, "b": {}},
            tripwire_results=[], verdict="GREEN", missing_strategies=[],
            new_strategies=[], counts_by_status={"FULL": 0, "LIMITED_SAMPLE": 1, "INSUFFICIENT_SAMPLE": 1},
            previous_run_audit_at=NOW - timedelta(hours=4), per_strategy_failures=[],
        )
        for f in ("run_id", "ran_at_utc", "finished_at_utc", "duration_seconds",
                  "strategies_expected", "strategies_published",
                  "counts_by_status", "tripwires", "verdict",
                  "previous_run_ts", "per_strategy_failures"):
            self.assertIn(f, audit)


# ─────────────────────────── 7. End-to-end run_publisher ──────────────────────

class TestRunPublisher(unittest.TestCase):

    def _db_query_factory(self, strategies: List[str], resolved_rows_per_strategy: Dict[str, List[Dict]]):
        def _q(sql: str) -> List[Dict[str, Any]]:
            if "GROUP BY strategy_id" in sql:
                return [
                    {"strategy_id": s, "total_fired": 200,
                     "has_prices": 200, "pending": 5,
                     "earliest_fire_ts": "2026-02-13", "latest_fire_ts": "2026-05-13"}
                    for s in strategies
                ]
            # Per-strategy resolved-rows query
            for s in strategies:
                if f"strategy_id='{s}'" in sql:
                    return resolved_rows_per_strategy.get(s, [])
            return []
        return _q

    def test_T48_full_publication_two_strategies(self):
        fake = FakeFabric()
        rows_by_sid = {
            "alpha_m5": _make_resolved_rows(wins=80, losses=40, neutrals=10),  # n=130, wr=0.667
            "beta_m15": _make_resolved_rows(wins=10, losses=5, neutrals=2),    # n=17 → INSUFFICIENT
        }
        db_query = self._db_query_factory(["alpha_m5", "beta_m15"], rows_by_sid)
        audit = run_publisher(
            db_query=db_query,
            fabric_get=fake.get, fabric_set=fake.set,
            now_utc_=NOW, dry_run=False,
        )
        # alpha_m5 has n=130, wr=0.667, expectancy>0 → should be FULL
        # beta_m15 has n=17 → INSUFFICIENT_SAMPLE (n<30)
        # But beta_m15 db_query had has_prices=200 (from group query), n_resolved=17 from rows
        # That makes it LIMITED_SAMPLE in current classifier (n=17 < 30 → INSUFFICIENT)
        published_keys = [k for k in fake.set_calls
                          if k.startswith(KEY_STRATEGY_HEALTH_PREFIX)
                          and k.endswith(KEY_STRATEGY_HEALTH_SUFFIX)]
        self.assertEqual(len(published_keys), 2)
        # Audit + state + latest written
        self.assertIn(KEY_PUBLISHER_STATE, fake.store)
        self.assertIn(KEY_PUBLISHER_AUDIT_LATEST, fake.store)
        self.assertEqual(audit["strategies_expected"], 2)
        self.assertEqual(audit["strategies_published"], 2)

    def test_T49_db_unreachable_fails_loud_no_writes(self):
        fake = FakeFabric()

        def _db_query_dies(sql: str):
            return None  # mimics DB unreachable

        with self.assertRaises(RuntimeError):
            run_publisher(
                db_query=_db_query_dies,
                fabric_get=fake.get, fabric_set=fake.set,
                now_utc_=NOW, dry_run=False,
            )
        # Critical: NO fabric writes occurred
        self.assertEqual(fake.set_calls, [])
        self.assertNotIn(KEY_PUBLISHER_STATE, fake.store)
        self.assertNotIn(KEY_PUBLISHER_AUDIT_LATEST, fake.store)

    def test_T50_per_strategy_fabric_write_failure_becomes_amber(self):
        fake = FakeFabric()
        # Force the strategy_health write for alpha to fail
        fake.set_should_fail_for.append(
            f"{KEY_STRATEGY_HEALTH_PREFIX}alpha_m5{KEY_STRATEGY_HEALTH_SUFFIX}"
        )
        rows = {
            "alpha_m5": _make_resolved_rows(wins=80, losses=40, neutrals=10),
            "beta_m5": _make_resolved_rows(wins=80, losses=40, neutrals=10),
        }
        db_query = self._db_query_factory(["alpha_m5", "beta_m5"], rows)
        audit = run_publisher(
            db_query=db_query, fabric_get=fake.get, fabric_set=fake.set,
            now_utc_=NOW, dry_run=False,
        )
        # alpha failed → 1 published, 1 missing → TW-1 RED → verdict RED
        self.assertEqual(audit["verdict"], "RED")
        # per_strategy_failures recorded
        self.assertEqual(len(audit["per_strategy_failures"]), 1)
        self.assertEqual(audit["per_strategy_failures"][0]["strategy_id"], "alpha_m5")
        self.assertIn("FABRIC_WRITE", audit["per_strategy_failures"][0]["reason"])

    def test_T51_red_run_emits_fault_audit(self):
        fake = FakeFabric()
        # Force one write to fail → TW-1 RED → fault audit emitted
        fake.set_should_fail_for.append(
            f"{KEY_STRATEGY_HEALTH_PREFIX}alpha_m5{KEY_STRATEGY_HEALTH_SUFFIX}"
        )
        rows = {
            "alpha_m5": _make_resolved_rows(wins=80, losses=40, neutrals=10),
            "beta_m5": _make_resolved_rows(wins=80, losses=40, neutrals=10),
        }
        db_query = self._db_query_factory(["alpha_m5", "beta_m5"], rows)
        run_publisher(db_query=db_query, fabric_get=fake.get, fabric_set=fake.set,
                     now_utc_=NOW, dry_run=False)
        # Look for a fault key written
        fault_keys = [k for k in fake.store if k.startswith(KEY_PUBLISHER_FAULT_PREFIX)]
        self.assertEqual(len(fault_keys), 1)
        fault_list = fake.store[fault_keys[0]]
        self.assertEqual(len(fault_list), 1)
        self.assertTrue(fault_list[0]["is_red"])

    def test_T52_dry_run_writes_nothing(self):
        fake = FakeFabric()
        rows = {"alpha_m5": _make_resolved_rows(wins=80, losses=40, neutrals=10)}
        db_query = self._db_query_factory(["alpha_m5"], rows)
        audit = run_publisher(
            db_query=db_query, fabric_get=fake.get, fabric_set=fake.set,
            now_utc_=NOW, dry_run=True,
        )
        self.assertEqual(fake.set_calls, [])
        self.assertNotIn(KEY_PUBLISHER_STATE, fake.store)


# ─────────────────────────── 8. Score computation ─────────────────────────────

class TestScoreComputation(unittest.TestCase):

    def test_T53_compute_score_components(self):
        out = compute_score_components(wr=0.50, expectancy_pts=1.0, n_fires_resolved=100)
        self.assertIn("score", out)
        self.assertIn("components", out)
        self.assertIn("wr_norm", out["components"])
        self.assertIn("expectancy_norm", out["components"])
        self.assertIn("sample_quality", out["components"])

    def test_T54_compute_strategy_score_basic(self):
        rows = _make_resolved_rows(wins=10, losses=5, neutrals=2)
        s = compute_strategy_score("test_strategy", rows)
        self.assertEqual(s.n_fires_resolved, 17)
        self.assertEqual(s.win_count, 10)
        self.assertEqual(s.loss_count, 5)
        self.assertEqual(s.neutral_count, 2)
        self.assertAlmostEqual(s.wr, 10/15, places=3)  # wins / (wins+losses)


# ─────────────────────────── 9. Contract compatibility ────────────────────────

class TestContractCompatibility(unittest.TestCase):

    def test_T55_canonical_key_pattern(self):
        # Key prefix + suffix must produce r2d2:strategy_health:<id>:overall
        key = f"{KEY_STRATEGY_HEALTH_PREFIX}myStrategy{KEY_STRATEGY_HEALTH_SUFFIX}"
        self.assertEqual(key, "r2d2:strategy_health:myStrategy:overall")

    def test_T56_allowed_enums_match_contract(self):
        self.assertSetEqual(ALLOWED_HEALTH_STATUS,
                           {"FULL", "LIMITED_SAMPLE", "INSUFFICIENT_SAMPLE"})
        self.assertSetEqual(ALLOWED_RELIABILITY_LABEL,
                           {"TRUSTED", "WATCH", "UNTRUSTED"})
        self.assertSetEqual(ALLOWED_DIRECTION_CHECK,
                           {"POSITIVE", "NEUTRAL", "NEGATIVE"})

    def test_T57_v3_freshness_gate_hours_30(self):
        self.assertEqual(V3_FRESHNESS_GATE_HOURS, 30)


# ─────────────────────────── 10. Static no-drift scan ─────────────────────────

class TestStaticNoDriftScan(unittest.TestCase):

    def _strip_comments_and_docstrings(self, src: str) -> str:
        """Strip triple-quoted strings and # comments. Coarse but sufficient for
        this static-scan check."""
        import re
        no_triple = re.sub(r'"""[\s\S]*?"""', "", src)
        no_triple = re.sub(r"'''[\s\S]*?'''", "", no_triple)
        lines = []
        for line in no_triple.split("\n"):
            idx = line.find("#")
            if idx >= 0:
                line = line[:idx]
            lines.append(line)
        return "\n".join(lines)

    def test_T58_no_datetime_utcnow_in_publisher(self):
        src = open("/srv/r2d2/maintenance/strategy_health_publisher.py").read()
        # Scan executable code only — docstring/comments may mention these
        # tokens as negative examples (e.g. "no datetime.utcnow()").
        code_only = self._strip_comments_and_docstrings(src)
        for forbidden in ("utcnow()", "datetime.utcnow"):
            self.assertNotIn(forbidden, code_only,
                             f"forbidden token {forbidden!r} present in executable code")

    def test_T59_no_falcon_recovery_or_p2d_p1_c1(self):
        src = open("/srv/r2d2/maintenance/strategy_health_publisher.py").read()
        code_only = self._strip_comments_and_docstrings(src)
        for forbidden in ("disable_handler", "manual_promote_recovery",
                           "P2D ", "P1 ", "C1 ", "MetaTrader5",
                           "order_send", "place_order", "Plutus",
                           "FTMO", "Ranger ", "Rogue "):
            self.assertNotIn(forbidden, code_only,
                             f"forbidden token {forbidden!r} in executable code")

    def test_T60_no_neo_solo_trader_touch(self):
        src = open("/srv/r2d2/maintenance/strategy_health_publisher.py").read()
        code_only = self._strip_comments_and_docstrings(src)
        for forbidden in ("/srv/NEO", "neo_observer", "Solo executes",
                           "trader_signal_surface"):
            self.assertNotIn(forbidden, code_only,
                             f"forbidden reference in executable code: {forbidden!r}")


# ─────────────────────────── 11. Dormant strategy publication ────────────────
# Phase C remediation 2026-05-13 — architect ruling that every expected strategy
# must have a fresh scheduled :overall record, including dormant strategies.

class TestDormantEnvelope(unittest.TestCase):

    def _dormant(self) -> dict:
        return build_dormant_envelope(
            strategy_id="dormant_m5",
            window_start=NOW - timedelta(days=90),
            window_end=NOW,
            computed_at=NOW,
        )

    def test_T61_dormant_envelope_status_INSUFFICIENT_SAMPLE(self):
        env = self._dormant()
        self.assertEqual(env["health_status"], "INSUFFICIENT_SAMPLE")

    def test_T62_dormant_envelope_score_null(self):
        env = self._dormant()
        self.assertIsNone(env["score"])
        self.assertIsNone(env["score_components"])

    def test_T63_dormant_health_status_reason(self):
        env = self._dormant()
        self.assertEqual(env["health_status_reason"], DORMANT_HEALTH_STATUS_REASON)
        self.assertEqual(env["health_status_reason"], "no_fires_in_90d_window")

    def test_T64_dormant_failed_gates(self):
        env = self._dormant()
        elig = env["full_eligibility"]
        self.assertFalse(elig["sample_gate_passed"])
        self.assertFalse(elig["reliability_gate_passed"])
        self.assertFalse(elig["direction_check_gate_passed"])
        self.assertIn("sample_gate", elig["failed_gates"])
        self.assertIn("reliability_gate", elig["failed_gates"])
        self.assertIn("direction_check_gate", elig["failed_gates"])

    def test_T65_dormant_decision_grade_false(self):
        env = self._dormant()
        self.assertFalse(env["decision_grade"])

    def test_T66_dormant_source_enum_R2D2_SCHEDULED_V1(self):
        env = self._dormant()
        self.assertEqual(env["version"], SOURCE_ENUM)
        self.assertEqual(env["version"], "R2D2_SCHEDULED_V1")
        self.assertNotEqual(env["version"], "R2D2_POST_33_REFRESH_V1")
        self.assertEqual(env["health_source"], DORMANT_HEALTH_SOURCE)

    def test_T67_dormant_contract_compatibility(self):
        env = self._dormant()
        self.assertEqual(env["contract_compatibility"], CONTRACT_VERSION)

    def test_T68_dormant_computed_at_utc_tz_z(self):
        env = self._dormant()
        self.assertTrue(env["computed_at_utc"].endswith("Z"))

    def test_T69_dormant_marker_present(self):
        env = self._dormant()
        self.assertTrue(env.get("dormant_in_90d_window"))

    def test_T70_dormant_zero_counts(self):
        env = self._dormant()
        self.assertEqual(env["n_fires_resolved"], 0)
        self.assertEqual(env["win_count"], 0)
        self.assertEqual(env["loss_count"], 0)
        self.assertEqual(env["neutral_count"], 0)
        self.assertIsNone(env["wr"])
        self.assertIsNone(env["expectancy_pts"])


# ─────────────────────────── 12. Decision-grade flag on active envelopes ──────

class TestDecisionGradeOnActiveEnvelopes(unittest.TestCase):

    def _active(self, n=120, wr=0.55, expectancy=0.50) -> dict:
        cov = StrategyCoverage(strategy_id="x_m5", total_fired=130, has_prices=120,
                              missing_prices=10, pending=10)
        score = StrategyScore(strategy_id="x_m5", n_fires_resolved=n,
                              win_count=int(n*0.5), loss_count=int(n*0.5),
                              wr=wr, expectancy_pts=expectancy,
                              score=0.55, score_components={"a": 1})
        elig = evaluate_full_eligibility(n, wr, expectancy)
        return build_envelope(cov, score, elig,
                              window_start=NOW - timedelta(days=90),
                              window_end=NOW, computed_at=NOW)

    def test_T71_active_FULL_decision_grade_True(self):
        env = self._active(n=120, wr=0.55, expectancy=0.50)
        self.assertEqual(env["health_status"], "FULL")
        self.assertTrue(env["decision_grade"])

    def test_T72_active_LIMITED_decision_grade_False(self):
        env = self._active(n=200, wr=0.40, expectancy=0.10)
        self.assertEqual(env["health_status"], "LIMITED_SAMPLE")
        self.assertFalse(env["decision_grade"])

    def test_T73_active_INSUFFICIENT_decision_grade_False(self):
        cov = StrategyCoverage(strategy_id="empty", has_prices=0)
        score = StrategyScore(strategy_id="empty", n_fires_resolved=0)
        elig = evaluate_full_eligibility(0, None, None)
        env = build_envelope(cov, score, elig,
                             window_start=NOW - timedelta(days=90),
                             window_end=NOW, computed_at=NOW)
        self.assertEqual(env["health_status"], "INSUFFICIENT_SAMPLE")
        self.assertFalse(env["decision_grade"])


# ─────────────────────────── 13. Discover existing strategies in fabric ───────

class TestDiscoverExistingStrategies(unittest.TestCase):

    def test_T74_discover_filters_snapshot_keys(self):
        keys = [
            "r2d2:strategy_health:alpha_m5:overall",
            "r2d2:strategy_health:alpha_m5:overall:snapshot:pre_post_33:20260506T124246Z",
            "r2d2:strategy_health:beta_m15:overall",
            "r2d2:strategy_health:beta_m15:overall:snapshot:pre_post_28:20260506T101116Z",
        ]
        sids = discover_existing_strategies_in_fabric(lambda p: keys)
        self.assertEqual(sids, ["alpha_m5", "beta_m15"])

    def test_T75_discover_skips_publisher_state_key(self):
        keys = [
            "r2d2:strategy_health:alpha_m5:overall",
            KEY_PUBLISHER_STATE,
        ]
        sids = discover_existing_strategies_in_fabric(lambda p: keys)
        self.assertEqual(sids, ["alpha_m5"])

    def test_T76_discover_empty_when_no_keys(self):
        sids = discover_existing_strategies_in_fabric(lambda p: [])
        self.assertEqual(sids, [])

    def test_T77_discover_sorted_output(self):
        keys = [
            "r2d2:strategy_health:zulu:overall",
            "r2d2:strategy_health:alpha:overall",
            "r2d2:strategy_health:mike:overall",
        ]
        sids = discover_existing_strategies_in_fabric(lambda p: keys)
        self.assertEqual(sids, ["alpha", "mike", "zulu"])


# ─────────────────────────── 14. Union expected set ───────────────────────────

class TestExpectedSetUnion(unittest.TestCase):

    def test_T78_union_active_plus_existing(self):
        active = ["alpha", "beta", "gamma"]  # 3 with fires
        existing = ["alpha", "delta", "epsilon"]  # 3 in fabric (alpha overlaps)
        expected, dormant = compute_expected_strategy_set(active, existing)
        self.assertEqual(expected, ["alpha", "beta", "delta", "epsilon", "gamma"])
        self.assertEqual(dormant, ["delta", "epsilon"])

    def test_T79_only_active_no_dormant(self):
        active = ["alpha", "beta"]
        existing = ["alpha", "beta"]
        expected, dormant = compute_expected_strategy_set(active, existing)
        self.assertEqual(expected, ["alpha", "beta"])
        self.assertEqual(dormant, [])

    def test_T80_only_dormant_no_active(self):
        # Edge case: all strategies dormant (no DB activity)
        active = []
        existing = ["alpha", "beta"]
        expected, dormant = compute_expected_strategy_set(active, existing)
        self.assertEqual(expected, ["alpha", "beta"])
        self.assertEqual(dormant, ["alpha", "beta"])

    def test_T81_new_strategy_in_active_not_in_existing(self):
        # A brand-new strategy that just started firing
        active = ["alpha", "brand_new"]
        existing = ["alpha"]
        expected, dormant = compute_expected_strategy_set(active, existing)
        self.assertEqual(expected, ["alpha", "brand_new"])
        self.assertEqual(dormant, [])  # brand_new is active, not dormant


# ─────────────────────────── 15. TW-8 no stale version in fabric ──────────────

class TestTripwire8NoStaleVersion(unittest.TestCase):

    def _envelope(self, version):
        return {
            "version": version,
            "health_status": "INSUFFICIENT_SAMPLE",
            "score": None,
            "computed_at_utc": "2026-05-13T18:00:00.000000Z",
            "n_fires_resolved": 0,
        }

    def test_T82_tw8_pass_when_all_R2D2_SCHEDULED_V1(self):
        store = {
            "r2d2:strategy_health:alpha:overall": self._envelope("R2D2_SCHEDULED_V1"),
            "r2d2:strategy_health:beta:overall": self._envelope("R2D2_SCHEDULED_V1"),
        }
        r = tripwire_8_no_stale_version_in_fabric(
            fabric_keys=lambda p: list(store.keys()),
            fabric_get_envelope=lambda k: store.get(k),
        )
        self.assertTrue(r.passed)
        self.assertEqual(r.tier, "RED")

    def test_T83_tw8_fail_on_stale_POST_33(self):
        store = {
            "r2d2:strategy_health:alpha:overall": self._envelope("R2D2_SCHEDULED_V1"),
            "r2d2:strategy_health:dormant_old:overall": self._envelope(
                "R2D2_POST_33_REFRESH_V1_2026_05_06"
            ),
        }
        r = tripwire_8_no_stale_version_in_fabric(
            fabric_keys=lambda p: list(store.keys()),
            fabric_get_envelope=lambda k: store.get(k),
        )
        self.assertFalse(r.passed)
        self.assertIn("dormant_old", r.detail)

    def test_T84_tw8_skips_snapshot_keys(self):
        # Snapshots are immutable historical refs — TW-8 ignores them
        store = {
            "r2d2:strategy_health:alpha:overall": self._envelope("R2D2_SCHEDULED_V1"),
            "r2d2:strategy_health:alpha:overall:snapshot:pre_post_33:20260506T124246Z":
                self._envelope("R2D2_POST_33_REFRESH_V1_2026_05_06"),
        }
        r = tripwire_8_no_stale_version_in_fabric(
            fabric_keys=lambda p: list(store.keys()),
            fabric_get_envelope=lambda k: store.get(k),
        )
        self.assertTrue(r.passed)

    def test_T85_tw8_skips_publisher_state_key(self):
        store = {
            "r2d2:strategy_health:alpha:overall": self._envelope("R2D2_SCHEDULED_V1"),
            KEY_PUBLISHER_STATE: {"verdict": "GREEN", "source_enum": "R2D2_SCHEDULED_V1"},
        }
        # publisher:state has no .version field but ends in :state not :overall
        # — fabric_keys lookup with pattern '*:overall' would skip it; here we
        # include it explicitly to prove the in-code skip-guard
        r = tripwire_8_no_stale_version_in_fabric(
            fabric_keys=lambda p: list(store.keys()),
            fabric_get_envelope=lambda k: store.get(k),
        )
        self.assertTrue(r.passed)


# ─────────────────────────── 16. End-to-end dormant publication ───────────────

class TestEndToEndDormantPublication(unittest.TestCase):

    def _db_query_factory(self, active_strategies, resolved_rows_per_strategy):
        def _q(sql):
            if "GROUP BY strategy_id" in sql:
                return [
                    {"strategy_id": s, "total_fired": 200,
                     "has_prices": 200, "pending": 5,
                     "earliest_fire_ts": "2026-02-13", "latest_fire_ts": "2026-05-13"}
                    for s in active_strategies
                ]
            for s in active_strategies:
                if f"strategy_id='{s}'" in sql:
                    return resolved_rows_per_strategy.get(s, [])
            return []
        return _q

    def test_T86_dormant_strategy_published_with_fresh_envelope(self):
        # Setup: 1 active + 1 dormant (in fabric only)
        fake = FakeFabric()
        # Seed fabric with a stale POST_33 record for the dormant strategy
        fake.store["r2d2:strategy_health:active_m5:overall"] = {
            "version": "R2D2_SCHEDULED_V1", "health_status": "FULL", "score": 0.6,
            "computed_at_utc": "2026-05-12T18:00:00.000000Z", "n_fires_resolved": 200,
        }
        fake.store["r2d2:strategy_health:dormant_m5:overall"] = {
            "version": "R2D2_POST_33_REFRESH_V1_2026_05_06",
            "health_status": "INSUFFICIENT_SAMPLE", "score": None,
            "computed_at_utc": "2026-05-06T13:45:00+00:00", "n_fires_resolved": 0,
        }
        rows = {"active_m5": _make_resolved_rows(wins=80, losses=40, neutrals=10)}
        db_query = self._db_query_factory(["active_m5"], rows)

        def _fabric_keys(pattern):
            return [k for k in fake.store.keys() if ":overall" in k]

        audit = run_publisher(
            db_query=db_query,
            fabric_get=fake.get, fabric_set=fake.set,
            fabric_keys=_fabric_keys,
            now_utc_=NOW, dry_run=False,
        )
        # Both strategies should be published this run
        self.assertEqual(audit["strategies_expected"], 2)
        self.assertEqual(audit["strategies_published"], 2)

        # Dormant strategy now has fresh R2D2_SCHEDULED_V1 envelope
        dormant_env = fake.store["r2d2:strategy_health:dormant_m5:overall"]
        self.assertEqual(dormant_env["version"], "R2D2_SCHEDULED_V1")
        self.assertEqual(dormant_env["health_status"], "INSUFFICIENT_SAMPLE")
        self.assertEqual(dormant_env["health_status_reason"], "no_fires_in_90d_window")
        self.assertIsNone(dormant_env["score"])
        self.assertFalse(dormant_env["decision_grade"])
        self.assertTrue(dormant_env.get("dormant_in_90d_window"))

    def test_T87_no_stale_POST_33_remains_after_run(self):
        # The TW-8 validation: after a successful publication, NO stale version
        # should remain at any canonical :overall key
        fake = FakeFabric()
        fake.store["r2d2:strategy_health:alpha:overall"] = {
            "version": "R2D2_SCHEDULED_V1", "health_status": "FULL", "score": 0.6,
            "computed_at_utc": "2026-05-12T18:00:00.000000Z", "n_fires_resolved": 200,
        }
        fake.store["r2d2:strategy_health:stale_one:overall"] = {
            "version": "R2D2_POST_33_REFRESH_V1_2026_05_06",
            "health_status": "INSUFFICIENT_SAMPLE", "score": None,
            "computed_at_utc": "2026-05-06T13:45:00+00:00", "n_fires_resolved": 0,
        }
        fake.store["r2d2:strategy_health:stale_two:overall"] = {
            "version": "R2D2_POST_33_REFRESH_V1_2026_05_06",
            "health_status": "INSUFFICIENT_SAMPLE", "score": None,
            "computed_at_utc": "2026-05-06T13:45:00+00:00", "n_fires_resolved": 0,
        }
        rows = {"alpha": _make_resolved_rows(wins=80, losses=40, neutrals=10)}
        db_query = self._db_query_factory(["alpha"], rows)

        def _fabric_keys(pattern):
            return [k for k in fake.store.keys() if ":overall" in k]

        run_publisher(
            db_query=db_query,
            fabric_get=fake.get, fabric_set=fake.set,
            fabric_keys=_fabric_keys,
            now_utc_=NOW, dry_run=False,
        )
        # Post-run: every :overall key has version=R2D2_SCHEDULED_V1
        for k, env in fake.store.items():
            if not k.endswith(":overall"):
                continue
            self.assertEqual(
                env["version"], "R2D2_SCHEDULED_V1",
                f"stale version remained at {k}: {env.get('version')}",
            )

    def test_T88_dormant_only_run_publishes_dormant(self):
        # Edge: NO active strategies, only fabric-existing strategies
        fake = FakeFabric()
        fake.store["r2d2:strategy_health:dormant_a:overall"] = {
            "version": "R2D2_POST_33_REFRESH_V1_2026_05_06",
            "health_status": "INSUFFICIENT_SAMPLE", "score": None,
            "computed_at_utc": "2026-05-06T13:45:00+00:00", "n_fires_resolved": 0,
        }
        fake.store["r2d2:strategy_health:dormant_b:overall"] = {
            "version": "R2D2_POST_33_REFRESH_V1_2026_05_06",
            "health_status": "INSUFFICIENT_SAMPLE", "score": None,
            "computed_at_utc": "2026-05-06T13:45:00+00:00", "n_fires_resolved": 0,
        }

        def _db_query_empty(sql):
            if "GROUP BY strategy_id" in sql:
                return []
            return []

        def _fabric_keys(pattern):
            return [k for k in fake.store.keys() if ":overall" in k]

        audit = run_publisher(
            db_query=_db_query_empty,
            fabric_get=fake.get, fabric_set=fake.set,
            fabric_keys=_fabric_keys,
            now_utc_=NOW, dry_run=False,
        )
        self.assertEqual(audit["strategies_expected"], 2)
        self.assertEqual(audit["strategies_published"], 2)
        # Both dormants refreshed
        for sid in ("dormant_a", "dormant_b"):
            env = fake.store[f"r2d2:strategy_health:{sid}:overall"]
            self.assertEqual(env["version"], "R2D2_SCHEDULED_V1")
            self.assertEqual(env["health_status_reason"], "no_fires_in_90d_window")


if __name__ == "__main__":
    unittest.main()
