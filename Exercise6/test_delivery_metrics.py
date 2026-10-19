import random
import unittest

from delivery_metrics import sample_metrics


class SampleMetricsTests(unittest.TestCase):
    def test_normal_values_stay_below_alert_thresholds(self):
        sample = sample_metrics("normal", 101, random.Random(1))

        self.assertEqual(sample["total"], 101)
        self.assertLessEqual(sample["pending"], 40)
        self.assertLessEqual(sample["average_time_minutes"], 45)

    def test_high_pending_scenario_exceeds_pending_threshold_only(self):
        sample = sample_metrics("high_pending", 101, random.Random(1))

        self.assertGreater(sample["pending"], 40)
        self.assertLessEqual(sample["average_time_minutes"], 45)

    def test_long_delivery_scenario_exceeds_time_threshold_only(self):
        sample = sample_metrics("long_delivery", 101, random.Random(1))

        self.assertGreater(sample["average_time_minutes"], 45)
        self.assertLessEqual(sample["pending"], 40)


if __name__ == "__main__":
    unittest.main()
