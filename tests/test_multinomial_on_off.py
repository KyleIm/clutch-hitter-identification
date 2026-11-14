import sys
import unittest
from pathlib import Path
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "Script"))
from multinomial_on_off import fit_weighted_on_off as fit
from lima_histogram_RISP_sample import binomial_on_off_s
from validate_weighted_on_off import verify_reduction


class MultinomialTests(unittest.TestCase):
    def test_equal_mean_distinct_distributions(self):
        result = fit([50, 0, 50], [0, 100, 0], [0, 1, 2])
        self.assertEqual(result.score, 0)
        np.testing.assert_array_equal(result.null_probabilities[1], [0, 1, 0])

    def test_boundary_uses_unobserved_extreme(self):
        result = fit([10, 0, 0], [0, 10, 0], [0, 1, 2])
        self.assertAlmostEqual(result.ts, 20 * np.log(2))
        np.testing.assert_allclose(result.null_probabilities, [[.5, 0, .5], [0, 1, 0]])

    def test_affine_invariance_and_sign_symmetry(self):
        on, off, weights = [18, 2, 1, 0], [7000, 20, 0, 50], np.array([0, .7, 1.6, 2])
        score = fit(on, off, weights).score
        self.assertAlmostEqual(score, -fit(off, on, weights).score, places=9)
        self.assertAlmostEqual(score, fit(on, off, 7*weights + 3).score, places=9)
        self.assertAlmostEqual(score, fit(on, off, weights*10).score, places=9)

    def test_binomial_with_sparse_and_highly_unequal_counts(self):
        for a, b in (([10,0,0], [0,8,2]), ([1,0,1],[99999,1,1]), ([4,0,0],[7,0,0])):
            self.assertAlmostEqual(fit(a,b,[0,1,1]).score,
                binomial_on_off_s(sum(a[1:]), a[0], sum(b[1:]), b[0]), delta=2e-7)

    def test_empty_and_identical(self):
        self.assertTrue(np.isnan(fit([0,0],[0,8],[0,1]).score))
        self.assertTrue(np.isnan(fit([0,8],[0,0],[0,1]).score))
        self.assertEqual(fit([1,2,3],[2,4,6],[0,1,2]).score, 0)

    def test_existing_retrosheet_reduction(self):
        self.assertEqual(verify_reduction().players.tolist(), [5716, 5716])
