import sys
import unittest
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "Script"))
from binomial_upper_limit import binomial_upper_limit


class UpperLimitTests(unittest.TestCase):
    def test_symmetric_rates_and_sample_size(self):
        small = binomial_upper_limit(3, 10, 3, 10)
        large = binomial_upper_limit(300, 1000, 300, 1000)
        self.assertAlmostEqual(small.positive_probability, .5, places=10)
        self.assertAlmostEqual(large.positive_probability, .5, places=10)
        self.assertLess(large.upper_limit, small.upper_limit)

    def test_reflection_and_custom_level(self):
        forward = binomial_upper_limit(7, 10, 3, 10, .8)
        backward = binomial_upper_limit(3, 10, 7, 10)
        self.assertAlmostEqual(forward.positive_probability + backward.positive_probability, 1)
        self.assertAlmostEqual(forward.conditional_probability, .8, places=9)
        self.assertLess(backward.upper_limit, forward.upper_limit)

    def test_opposite_boundaries_with_underflow(self):
        result = binomial_upper_limit(0, 1000, 1000, 1000)
        self.assertEqual(result.positive_probability, 0)
        self.assertLess(result.log_positive_probability, -1000)
        self.assertAlmostEqual(result.upper_limit, -np.expm1(np.log(.05)/2002), places=12)

    def test_sparse_all_hits_zero_hits_and_imbalance(self):
        for counts in ((1, 1, 1, 1), (0, 1, 0, 1), (0, 1, 4000, 13000), (13000, 13000, 1, 1)):
            with self.subTest(counts=counts):
                result = binomial_upper_limit(*counts)
                self.assertTrue(0 < result.upper_limit < 1)
                self.assertAlmostEqual(result.conditional_probability, .95, places=8)

    def test_invalid_counts_and_level(self):
        for counts in ((0, 0, 1, 2), (1, 2, 0, 0), (3, 2, 1, 2), (1.0, 2, 1, 2)):
            with self.subTest(counts=counts), self.assertRaises(ValueError):
                binomial_upper_limit(*counts)
        with self.assertRaises(ValueError):
            binomial_upper_limit(1, 2, 1, 2, 1)
