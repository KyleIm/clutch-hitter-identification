import sys
import unittest
from pathlib import Path
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "Script"))
from analyze_weighted_baseline import DATA, ROOT, pooled, score_players


class WeightedBaselineIntegrationTests(unittest.TestCase):
    def test_real_players_keep_counts_and_original_scores(self):
        weights = pd.read_csv(DATA / "fixed_weights.csv").set_index("outcome").weight
        prior = pd.read_csv(ROOT / "Results/RISP_LIPS/players.csv")
        for situation in ("risp", "lips"):
            counts = pd.read_csv(DATA / f"{situation}_player_counts.csv")
            groups = counts.on_eligible.gt(0) & counts.off_eligible.gt(0)
            example = counts.loc[groups & counts.total_pa.ge(2000)].head(12)
            example = pd.concat([example, counts.loc[~groups].head(1)])
            result = score_players(example, prior[prior.batter.isin(example.batter)],
                                   situation, weights)
            self.assertEqual(result.status.eq("empty_group").sum(), 1)
            self.assertEqual(result.status.eq("ok").sum(), 12)
            pd.testing.assert_frame_equal(result[example.columns],
                                          example.sort_values("batter").reset_index(drop=True))
            expected = prior.set_index("batter").loc[result.batter, f"score_{situation}"]
            np.testing.assert_array_equal(result.binomial_score, expected)
            np.testing.assert_allclose(result.weighted_score**2, result.weighted_ts)
            def fail(*args):
                raise RuntimeError("test optimizer failure")
            failed = score_players(example, prior[prior.batter.isin(example.batter)],
                                   situation, weights, solver=fail)
            self.assertEqual(failed.status.eq("optimizer_failure").sum(), 12)
            self.assertTrue(failed.weighted_score.isna().all())
            for summary in pooled(counts, weights):
                total = summary["on_trials"] + summary["off_trials"]
                self.assertEqual(total, 4569453 if summary["metric"] == "hit_rate" else 5019958)
