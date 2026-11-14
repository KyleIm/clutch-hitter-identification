import sys
import unittest
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "Script"))
from analyze_clutch_regression import analytical_r2, cross_validate, fit_ols


class ClutchRegressionTests(unittest.TestCase):
    def setUp(self):
        rng = np.random.default_rng(142)
        self.x = rng.normal(size=(31, 2))
        self.y = 2 + self.x @ [0.6, -1.3] + rng.normal(size=31)

    def test_hc3_matches_leave_one_out_residual_formula(self):
        fit = fit_ols(self.x, self.y)
        design = np.column_stack((np.ones(len(self.y)), self.x))
        deleted = []
        for i in range(len(self.y)):
            keep = np.arange(len(self.y)) != i
            coef = np.linalg.lstsq(design[keep], self.y[keep], rcond=None)[0]
            deleted.append(self.y[i] - design[i] @ coef)
        weighted = np.linalg.pinv(design) * deleted
        np.testing.assert_allclose(fit.se, np.sqrt((weighted**2).sum(axis=1)))

    def test_correlation_identity_matches_fit(self):
        fit = fit_ols(self.x, self.y)
        r2 = 1 - np.var(fit.residual) / np.var(self.y)
        self.assertAlmostEqual(analytical_r2(self.x, self.y)[-1], r2)

    def test_cross_validation_uses_training_only(self):
        folds = np.arange(len(self.y)) % 5
        pred, scores = cross_validate(self.x, self.y, folds)
        self.assertEqual(len(scores), 5)
        for fold in range(5):
            held = folds == fold
            x_train = np.column_stack((np.ones((~held).sum()), self.x[~held]))
            coef = np.linalg.lstsq(x_train, self.y[~held], rcond=None)[0]
            np.testing.assert_allclose(pred[held], coef[0] + self.x[held] @ coef[1:])
