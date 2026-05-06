"""Unit tests for correlation_tracker.

Tests cover:
- Spearman rho correctness (monotonic positive/negative/random/tied/constant)
- Threshold boundary conditions (n_WL, rho, expectancy)
- Direction label assignment per architect-approved thresholds
- TRUSTED threshold (5-criterion gate, informational only)
- Quarantine stickiness (tdr_m5, SF-002)
- Snapshot trigger logic
- Discord severity gates
- No promotion / no auto-lift / no V3-H3 change

Read-only — no fabric or DB writes during tests.
"""
import sys
import unittest

sys.path.insert(0, "/opt/r2d2/maintenance")
sys.path.insert(0, "/srv/r2d2/maintenance")

from correlation_tracker import (
    spearman_rho,
    compute_per_strategy,
    assign_direction_label,
    check_trusted_threshold,
    should_snapshot,
    should_discord,
    _compute_r_multiple,
    QUARANTINED_STRATEGIES,
    R_MULTIPLE_STRATEGIES,
    N_WL_MIN,
    TRUSTED_N_WL,
)


class TestSpearmanRho(unittest.TestCase):

    def test_monotonic_positive(self):
        # Strict increasing relationship
        rho = spearman_rho([1, 2, 3, 4, 5], [10, 20, 30, 40, 50])
        self.assertAlmostEqual(rho, 1.0, places=4)

    def test_monotonic_negative(self):
        rho = spearman_rho([1, 2, 3, 4, 5], [50, 40, 30, 20, 10])
        self.assertAlmostEqual(rho, -1.0, places=4)

    def test_no_correlation_zigzag(self):
        # Zigzag pattern — non-monotonic, low rho expected
        rho = spearman_rho([1, 2, 3, 4, 5, 6], [3, 1, 5, 2, 6, 4])
        self.assertTrue(-0.5 < rho < 0.5,
                        msg=f"expected near-zero rho, got {rho}")

    def test_constant_x_returns_zero(self):
        rho = spearman_rho([5, 5, 5, 5], [1, 2, 3, 4])
        self.assertEqual(rho, 0.0)

    def test_constant_y_returns_zero(self):
        rho = spearman_rho([1, 2, 3, 4], [7, 7, 7, 7])
        self.assertEqual(rho, 0.0)

    def test_insufficient_sample(self):
        self.assertIsNone(spearman_rho([], []))
        self.assertIsNone(spearman_rho([1], [2]))

    def test_tied_ranks(self):
        rho = spearman_rho([1, 1, 2, 2, 3, 3], [1, 2, 3, 4, 5, 6])
        self.assertGreater(rho, 0.9)


class TestComputePerStrategy(unittest.TestCase):

    def _make_sample(self, conf_outcomes, metric_kind="stored_pnl_pts"):
        """Build a sample list from list of (confidence, outcome, pnl).

        Per post-2026-05-06 architect decision, sample uses `outcome_metric` field
        (either R-multiple for R_MULTIPLE_STRATEGIES or stored pnl_pts otherwise).
        """
        return [{"confidence": c, "outcome": o, "outcome_metric": p,
                 "outcome_metric_kind": metric_kind}
                for c, o, p in conf_outcomes]

    def test_insufficient_sample(self):
        sample = self._make_sample([(6, "TP1_HIT", 5.0)] * 10)
        m = compute_per_strategy("test", sample)
        self.assertEqual(m["n_WL"], 10)
        self.assertEqual(m["direction_label"] if "direction_label" in m else "INSUFFICIENT_SAMPLE",
                         "INSUFFICIENT_SAMPLE")

    def test_basic_metrics(self):
        sample = self._make_sample([(6, "TP1_HIT", 10.0)] * 15 + [(6, "SL_HIT", -5.0)] * 10)
        m = compute_per_strategy("test", sample)
        self.assertEqual(m["n_WL"], 25)
        self.assertEqual(m["wins"], 15)
        self.assertEqual(m["losses"], 10)
        self.assertEqual(m["win_rate"], 0.6)
        self.assertEqual(m["expectancy_pts"], 4.0)

    def test_inverse_high_conf_cohort_detected(self):
        # conf=6 cohort positive; conf=8 cohort negative — high-conf inverse
        sample = (self._make_sample([(6, "TP1_HIT", 10.0)] * 20)
                  + self._make_sample([(8, "SL_HIT", -10.0)] * 10))
        m = compute_per_strategy("test", sample)
        self.assertTrue(m["inverse_high_conf_cohort"])

    def test_no_inverse_high_conf_when_all_positive(self):
        sample = (self._make_sample([(6, "TP1_HIT", 5.0)] * 15 + [(6, "SL_HIT", -2.0)] * 5)
                  + self._make_sample([(8, "TP1_HIT", 8.0)] * 12 + [(8, "SL_HIT", -1.0)] * 3))
        m = compute_per_strategy("test", sample)
        self.assertFalse(m["inverse_high_conf_cohort"])


class TestDirectionLabels(unittest.TestCase):

    def _metrics(self, n=50, rho=0.4, exp=1.5, inverse_high_conf=False, sid="test"):
        return {
            "strategy_id": sid, "n_WL": n, "rho": rho,
            "expectancy_pts": exp, "inverse_high_conf_cohort": inverse_high_conf,
        }

    def test_insufficient_sample(self):
        m = self._metrics(n=10)
        self.assertEqual(assign_direction_label(m), "INSUFFICIENT_SAMPLE")

    def test_positive(self):
        m = self._metrics(rho=0.4, exp=1.5)
        self.assertEqual(assign_direction_label(m), "POSITIVE")

    def test_positive_blocked_by_inverse_high_conf(self):
        m = self._metrics(rho=0.4, exp=1.5, inverse_high_conf=True)
        self.assertNotEqual(assign_direction_label(m), "POSITIVE")

    def test_weak_positive(self):
        m = self._metrics(rho=0.15, exp=0.3)
        self.assertEqual(assign_direction_label(m), "WEAK_POSITIVE")

    def test_neutral(self):
        m = self._metrics(rho=0.05, exp=0.1)
        self.assertEqual(assign_direction_label(m), "NEUTRAL")

    def test_inverse_leaning(self):
        m = self._metrics(rho=-0.2, exp=-0.5)
        self.assertEqual(assign_direction_label(m), "INVERSE_LEANING")

    def test_inverse_confirmed(self):
        m = self._metrics(rho=-0.4, exp=-2.0)
        self.assertEqual(assign_direction_label(m), "INVERSE_CONFIRMED")

    def test_quarantined_stays_inverse_even_with_positive_surface(self):
        # tdr_m5 with surface positive metrics should still be flagged
        m = self._metrics(rho=0.05, exp=0.3, sid="tdr_m5")
        label = assign_direction_label(m)
        self.assertIn(label, ("INVERSE_CONFIRMED", "INVERSE_LEANING"))

    def test_quarantined_sf002_persistent(self):
        m = self._metrics(rho=-0.05, exp=-0.3, sid="SF-002")
        label = assign_direction_label(m)
        self.assertIn(label, ("INVERSE_CONFIRMED", "INVERSE_LEANING"))


class TestTrustedThreshold(unittest.TestCase):

    def _metrics(self, n=150, rho=0.4, exp=1.5, inverse_high_conf=False, sid="test"):
        return {
            "strategy_id": sid, "n_WL": n, "rho": rho,
            "expectancy_pts": exp, "inverse_high_conf_cohort": inverse_high_conf,
        }

    def _stable_history(self, base_rho=0.35):
        return [{"rho": base_rho}, {"rho": base_rho + 0.02}, {"rho": base_rho - 0.03}]

    def test_trusted_pass(self):
        m = self._metrics()
        ok, reason = check_trusted_threshold(m, self._stable_history())
        self.assertTrue(ok, msg=reason)

    def test_trusted_fails_low_n(self):
        m = self._metrics(n=50)
        ok, _ = check_trusted_threshold(m, self._stable_history())
        self.assertFalse(ok)

    def test_trusted_fails_negative_rho(self):
        m = self._metrics(rho=-0.1)
        ok, _ = check_trusted_threshold(m, self._stable_history())
        self.assertFalse(ok)

    def test_trusted_fails_low_expectancy(self):
        m = self._metrics(exp=0.4)
        ok, _ = check_trusted_threshold(m, self._stable_history())
        self.assertFalse(ok)

    def test_trusted_fails_inverse_high_conf(self):
        m = self._metrics(inverse_high_conf=True)
        ok, _ = check_trusted_threshold(m, self._stable_history())
        self.assertFalse(ok)

    def test_trusted_fails_quarantined_strategy(self):
        m = self._metrics(sid="tdr_m5")
        ok, _ = check_trusted_threshold(m, self._stable_history())
        self.assertFalse(ok)

    def test_trusted_fails_unstable_history(self):
        m = self._metrics()
        unstable = [{"rho": 0.5}, {"rho": 0.1}, {"rho": 0.5}]  # large swings
        ok, _ = check_trusted_threshold(m, unstable)
        self.assertFalse(ok)

    def test_trusted_fails_insufficient_history(self):
        m = self._metrics()
        ok, _ = check_trusted_threshold(m, [{"rho": 0.4}])  # only 1 prior
        self.assertFalse(ok)


class TestSnapshotTrigger(unittest.TestCase):

    def test_first_run_always_snapshots(self):
        self.assertTrue(should_snapshot({"direction_label": "POSITIVE"}, None))

    def test_label_change_triggers(self):
        self.assertTrue(should_snapshot(
            {"direction_label": "INVERSE_CONFIRMED", "rho_delta_d1": 0.0},
            {"direction_label": "POSITIVE"}
        ))

    def test_rho_delta_above_threshold_triggers(self):
        self.assertTrue(should_snapshot(
            {"direction_label": "POSITIVE", "rho_delta_d1": 0.15},
            {"direction_label": "POSITIVE"}
        ))

    def test_no_change_no_snapshot(self):
        self.assertFalse(should_snapshot(
            {"direction_label": "POSITIVE", "rho_delta_d1": 0.05},
            {"direction_label": "POSITIVE"}
        ))


class TestDiscordSeverity(unittest.TestCase):

    def test_new_inverse_confirmed_triggers(self):
        m = {"strategy_id": "x", "direction_label": "INVERSE_CONFIRMED",
             "rho_delta_d7": 0, "expectancy_delta_d7": 0}
        should_post, _ = should_discord(m, prior_label="WATCH")
        self.assertTrue(should_post)

    def test_inverse_to_inverse_no_new_alert(self):
        m = {"strategy_id": "x", "direction_label": "INVERSE_CONFIRMED",
             "rho_delta_d7": 0, "expectancy_delta_d7": 0}
        should_post, _ = should_discord(m, prior_label="INVERSE_CONFIRMED")
        self.assertFalse(should_post)

    def test_trusted_threshold_reached_triggers(self):
        m = {"strategy_id": "x", "direction_label": "POSITIVE",
             "trusted_threshold_reached": True,
             "rho_delta_d7": 0, "expectancy_delta_d7": 0}
        should_post, _ = should_discord(m, prior_label="POSITIVE")
        self.assertTrue(should_post)

    def test_sharp_rho_degradation_triggers(self):
        m = {"strategy_id": "x", "direction_label": "WEAK_POSITIVE",
             "rho_delta_d7": -0.30, "expectancy_delta_d7": 0}
        should_post, _ = should_discord(m, prior_label="WEAK_POSITIVE")
        self.assertTrue(should_post)

    def test_sharp_expectancy_degradation_triggers(self):
        m = {"strategy_id": "x", "direction_label": "WEAK_POSITIVE",
             "rho_delta_d7": 0, "expectancy_delta_d7": -1.5}
        should_post, _ = should_discord(m, prior_label="WEAK_POSITIVE")
        self.assertTrue(should_post)

    def test_normal_run_no_post(self):
        m = {"strategy_id": "x", "direction_label": "POSITIVE",
             "rho_delta_d7": 0.05, "expectancy_delta_d7": 0.1}
        should_post, _ = should_discord(m, prior_label="POSITIVE")
        self.assertFalse(should_post)


class TestQuarantinePreservation(unittest.TestCase):
    """Architect rule: tdr_m5 + SF-002 inverse quarantine cannot be auto-lifted."""

    def test_quarantine_set_correct(self):
        self.assertIn("tdr_m5", QUARANTINED_STRATEGIES)
        self.assertIn("SF-002", QUARANTINED_STRATEGIES)

    def test_trusted_blocked_for_quarantined(self):
        m = {"strategy_id": "tdr_m5", "n_WL": 200, "rho": 0.5,
             "expectancy_pts": 1.0, "inverse_high_conf_cohort": False}
        history = [{"rho": 0.5}, {"rho": 0.5}, {"rho": 0.5}]
        ok, reason = check_trusted_threshold(m, history)
        self.assertFalse(ok)
        self.assertIn("QUARANTINED", reason)


class TestRMultipleComputation(unittest.TestCase):
    """Architect-approved 2026-05-06: nowic_at_m15 evaluation uses R-multiple."""

    def test_r_multiple_strategies_set(self):
        self.assertIn("nowic_at_m15", R_MULTIPLE_STRATEGIES)

    def test_r_multiple_long_TP1_HIT(self):
        # LONG: entry=100, sl=99, tp1=102 → win = +2, sl_dist = 1, R = +2.0
        row = {"entry_price": 100, "sl_price": 99, "tp1_price": 102,
               "synth_sl": None, "synth_tp1": None,
               "direction": "LONG", "outcome": "TP1_HIT"}
        self.assertAlmostEqual(_compute_r_multiple(row), 2.0)

    def test_r_multiple_long_SL_HIT(self):
        # LONG: entry=100, sl=99, tp1=102 → loss = -1, sl_dist = 1, R = -1.0
        row = {"entry_price": 100, "sl_price": 99, "tp1_price": 102,
               "synth_sl": None, "synth_tp1": None,
               "direction": "LONG", "outcome": "SL_HIT"}
        self.assertAlmostEqual(_compute_r_multiple(row), -1.0)

    def test_r_multiple_short_TP1_HIT(self):
        # SHORT: entry=100, sl=101, tp1=98 → win = +2, sl_dist = 1, R = +2.0
        row = {"entry_price": 100, "sl_price": 101, "tp1_price": 98,
               "synth_sl": None, "synth_tp1": None,
               "direction": "SHORT", "outcome": "TP1_HIT"}
        self.assertAlmostEqual(_compute_r_multiple(row), 2.0)

    def test_r_multiple_short_SL_HIT(self):
        # SHORT: entry=100, sl=101, tp1=98 → loss = -1, sl_dist = 1, R = -1.0
        row = {"entry_price": 100, "sl_price": 101, "tp1_price": 98,
               "synth_sl": None, "synth_tp1": None,
               "direction": "SHORT", "outcome": "SL_HIT"}
        self.assertAlmostEqual(_compute_r_multiple(row), -1.0)

    def test_r_multiple_falls_back_to_synth(self):
        # Stored brackets NULL; synth populated
        row = {"entry_price": 100, "sl_price": None, "tp1_price": None,
               "synth_sl": 99, "synth_tp1": 102,
               "direction": "LONG", "outcome": "TP1_HIT"}
        self.assertAlmostEqual(_compute_r_multiple(row), 2.0)

    def test_r_multiple_returns_none_if_no_brackets(self):
        row = {"entry_price": 100, "sl_price": None, "tp1_price": None,
               "synth_sl": None, "synth_tp1": None,
               "direction": "LONG", "outcome": "TP1_HIT"}
        self.assertIsNone(_compute_r_multiple(row))

    def test_r_multiple_forex_precision_preserved(self):
        # AUD_USD-like: entry=0.7126, sl=0.7119, tp1=0.7140 → win = +0.0014, sl_dist = 0.0007, R = +2.0
        # Stored outcome_pnl_pts would round 0.0014 to 0.00 (DECIMAL(10,2))
        # R-multiple preserves the +2.0 ratio
        row = {"entry_price": 0.7126, "sl_price": 0.7119, "tp1_price": 0.7140,
               "synth_sl": None, "synth_tp1": None,
               "direction": "LONG", "outcome": "TP1_HIT"}
        self.assertAlmostEqual(_compute_r_multiple(row), 2.0, places=4)


if __name__ == "__main__":
    unittest.main()
