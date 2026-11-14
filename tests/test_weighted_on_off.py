import sys
import unittest
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "Script"))
from prepare_weighted_on_off import ELIGIBLE, classify, weighted_mean


class WeightedProductionTests(unittest.TestCase):
    def test_each_outcome_and_exclusion(self):
        counts = pd.DataFrame(
            [[int(i == j) for j in range(7)] for i in range(7)],
            columns=ELIGIBLE,
        )
        counts["excluded"] = 100
        self.assertEqual(weighted_mean(counts).tolist(), [0, .70, .70, .90, 1.25, 1.60, 2])
        self.assertTrue(pd.isna(weighted_mean(counts * 0).iloc[0]))

    def test_mixed_outcomes_and_classification(self):
        labels = classify(pd.Series(["field_error", "sac_fly", "walk", "home_run", "intent_walk"]))
        counts = labels.value_counts().reindex(ELIGIBLE, fill_value=0).to_frame().T
        self.assertEqual(labels.tolist(), ["zero", "zero", "ubb", "home_run", "excluded"])
        self.assertAlmostEqual(weighted_mean(counts).iloc[0], .675)
