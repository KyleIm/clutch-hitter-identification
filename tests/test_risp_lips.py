import sys
import unittest
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import chi2_contingency

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "Script"))

from analyze_risp_lips import count_categories, margins, simulate_null
from lima_histogram_RISP_sample import binomial_on_off_s


class StepOneTests(unittest.TestCase):
    def test_four_categories_and_exclusions(self):
        rows = pd.DataFrame({
            "batter": ["a"] * 5,
            "inning": [3, 3, 7, 7, 7],
            "bat_score": [0] * 5,
            "fld_score": [0] * 5,
            "runner_situation_start": ["empty"] * 5,
            "runner_situation_before_final_pitch": ["empty", "2B", "empty", "3B", "3B"],
            "events": ["single", "sac_fly", "double", "field_out", "walk"],
        })
        counts = count_categories(rows).loc["a"]
        for prefix, hits, trials, pa in [
            ("neither", 1, 1, 1), ("risp_only", 0, 1, 1),
            ("lips_only", 1, 1, 1), ("both", 0, 1, 2),
        ]:
            self.assertEqual(tuple(counts[f"{prefix}_{k}"] for k in ("hits", "trials", "pa")),
                             (hits, trials, pa))

    def test_margins_reuse_both(self):
        risp, lips = margins(np.array([1, 2, 3, 4]))
        np.testing.assert_array_equal(risp, [6, 4])
        np.testing.assert_array_equal(lips, [7, 3])

    def test_vector_score_matches_g_test(self):
        counts = np.array([[24, 76, 90, 210], [0, 10, 7, 3], [0, 10, 0, 20]])
        scores = binomial_on_off_s(*counts.T)
        for table, score in zip(counts[:2], scores):
            expected = chi2_contingency(table.reshape(2, 2), correction=False,
                                        lambda_="log-likelihood").statistic
            self.assertAlmostEqual(score ** 2, expected)
            self.assertLess(score, 0)
        self.assertEqual(scores[2], 0)
        self.assertTrue(np.isnan(binomial_on_off_s(0, 0, 1, 2)))

    def test_identical_situations_share_every_draw(self):
        trials = np.array([[30, 0, 0, 15], [90, 0, 0, 20], [70, 0, 0, 50]])
        hits = trials // 4
        samples = simulate_null(hits, trials, {2000: np.ones(3, dtype=bool)}, 17, 71)
        np.testing.assert_allclose(samples[2000], 1)
