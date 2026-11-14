import sys
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "Script"))
from analyze_weighted_benchmark import BENCHMARKS, CUTOFFS, SCORES, TARGET, load_samples, run_models


class WeightedBenchmarkTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.players, cls.samples = load_samples()

    def test_samples_and_original_fold_alignment(self):
        self.assertEqual(self.players.batter.nunique(), 5716)
        for cutoff, (sample, folds, old) in self.samples.items():
            self.assertEqual(len(sample), CUTOFFS[cutoff])
            self.assertTrue(np.isfinite(sample[SCORES + BENCHMARKS]).all().all())
            saved = old[old.model.eq("Combined")]
            np.testing.assert_array_equal(sample.batter, saved.batter)
            np.testing.assert_array_equal(folds + 1, saved.fold)

    def test_reproduction_shared_folds_and_pooled_metrics(self):
        sample, folds, old = self.samples[2000]
        tables = {key: [] for key in ("coefficients", "performance", "cv_folds",
                                     "predictions", "diagnostics", "nested_comparisons")}
        results = run_models(sample, folds, old, 2000, tables)
        self.assertAlmostEqual(results["B3"]["pearson"], .443430562862173, places=10)
        self.assertAlmostEqual(results["B3"]["r2"], .196594403234271, places=10)
        self.assertAlmostEqual(tables["performance"][2]["r2"], .200535864117894, places=10)
        for frame in tables["predictions"]:
            np.testing.assert_array_equal(frame.fold, folds + 1)
            np.testing.assert_array_equal(frame.observed, sample[TARGET])
            y = frame.observed.to_numpy()
            e = y - frame.out_of_fold.to_numpy()
            metrics = results[frame.model.iloc[0]]
            self.assertAlmostEqual(metrics["r2"], 1 - np.mean(e**2)/np.var(y))
            self.assertAlmostEqual(metrics["rmse"], np.sqrt(np.mean(e**2)))
            self.assertAlmostEqual(metrics["mae"], np.mean(abs(e)))
