import sys
import unittest
from pathlib import Path

import numpy as np
from scipy import stats

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "Script"))
from analyze_external_benchmark import bootstrap, partial_pearson, williams


class ExternalBenchmarkTests(unittest.TestCase):
    def test_williams_reference_and_direction(self):
        # cocor's published example uses r.jk=.5, r.jh=.6, r.kh=.7, n=100.
        statistic, p = williams(.5, .6, .7, 100)
        reverse, reverse_p = williams(.6, .5, .7, 100)
        self.assertAlmostEqual(statistic, -reverse)
        self.assertAlmostEqual(p + reverse_p, 1)
        self.assertAlmostEqual(williams(.5, .5, .7, 100)[1], .5)
        self.assertGreater(p, .5)

    def test_bootstrap_resamples_all_metrics_together(self):
        rng = np.random.default_rng(44)
        values = rng.integers(0, 15, size=(40, 6))
        ids = np.random.default_rng(77).integers(40, size=(8, 40))
        result = bootstrap(values, 8, np.random.default_rng(77))
        for i, indices in enumerate(ids):
            sample = values[indices]
            for method, function in enumerate((stats.pearsonr, stats.spearmanr)):
                self.assertAlmostEqual(result[i, method, 0],
                                       function(sample[:, 0], sample[:, 4]).statistic)
                self.assertAlmostEqual(result[i, method, 2],
                                       function(sample[:, 1], sample[:, 4]).statistic)

    def test_partial_correlation_removes_linear_control(self):
        control = np.array([-3, -1, 1, 3])
        x = 10 * control + np.array([1, -1, -1, 1])
        y = 20 * control + np.array([1, -3, 3, -1])
        self.assertGreater(stats.pearsonr(x, y).statistic, .9)
        self.assertAlmostEqual(partial_pearson(x, y, control), 0)
