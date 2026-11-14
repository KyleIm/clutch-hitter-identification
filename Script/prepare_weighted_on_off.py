"""Prepare weighted-framework ON/OFF outcome counts from Retrosheet."""
import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from analyze_risp_lips import ROOT, RUNNER_COLUMN
from lima_histogram_RISP_sample import FAILURE_EVENTS, add_situation_flag

DATA = ROOT / "Data"
RESULTS = ROOT / "Results/Weighted_ON_OFF"
EVENTS = {
    **dict.fromkeys(FAILURE_EVENTS, "zero"),
    "walk": "ubb", "hit_by_pitch": "hbp", "single": "single",
    "double": "double", "triple": "triple", "home_run": "home_run",
    "intent_walk": "excluded", "sac_bunt": "excluded", "catcher_interf": "excluded",
}
OUTCOMES = list(dict.fromkeys(EVENTS.values()))
WEIGHTS = pd.Series({
    "zero": 0.00, "ubb": 0.70, "hbp": 0.70, "single": 0.90,
    "double": 1.25, "triple": 1.60, "home_run": 2.00,
}, name="weight")
ELIGIBLE = WEIGHTS.index.tolist()


def classify(events):
    labels = events.map(EVENTS)
    if labels.isna().any():
        raise ValueError(f"Unmapped events: {events[labels.isna()].unique().tolist()}")
    return labels


def weighted_mean(counts):
    eligible = counts[ELIGIBLE].sum(axis=1)
    return counts[ELIGIBLE].dot(WEIGHTS).div(eligible.where(eligible.gt(0)))


def prepare(out):
    out.mkdir(parents=True, exist_ok=True)
    season_parts = {"risp": [], "lips": []}
    columns = ["batter", "events", RUNNER_COLUMN, "runner_situation_start",
               "inning", "bat_score", "fld_score"]
    for year in range(1998, 2026):
        path = DATA / "Retrosheet/Compact" / f"mlb_{year}_plate_appearances_compact.csv"
        pa = pd.read_csv(path, usecols=columns)
        if pa.batter.isna().any():
            raise ValueError(f"Missing batter IDs in {path}")
        labels = classify(pa.events)
        for situation, parts in season_parts.items():
            on = add_situation_flag(pa, situation, RUNNER_COLUMN).is_risp
            parts.append(pa.groupby([pa.batter, on.rename("on"), labels.rename("outcome")]).size())
    prior = pd.read_csv(ROOT / "Results/RISP_LIPS/players.csv").set_index("batter")
    coverage = []
    for situation, parts in season_parts.items():
        counts = pd.concat(parts).groupby(level=[0, 1, 2]).sum().unstack([1, 2], fill_value=0)
        if set(counts.index) != set(prior.index):
            raise ValueError("Unexpected player IDs")
        counts = counts.reindex(prior.index)
        output = prior[["player_name", "total_pa"]].copy()
        for side, flag, previous in (("on", True, "n"), ("off", False, "b")):
            side_counts = counts[flag].reindex(columns=OUTCOMES, fill_value=0)
            np.testing.assert_array_equal(side_counts.sum(axis=1), prior[f"{previous}_{situation}"])
            np.testing.assert_array_equal(
                side_counts[["zero", "single", "double", "triple", "home_run"]].sum(axis=1),
                prior[f"{previous}_trials_{situation}"],
            )
            hits = side_counts[["single", "double", "triple", "home_run"]].sum(axis=1)
            np.testing.assert_array_equal(hits, prior[f"{previous}_success_{situation}"])
            eligible = side_counts[ELIGIBLE].sum(axis=1)
            output = output.join(side_counts.add_prefix(f"{side}_"))
            output[f"{side}_eligible"] = eligible
            output[f"{side}_weighted_mean"] = weighted_mean(side_counts)
        np.testing.assert_array_equal(
            output[["on_eligible", "off_eligible", "on_excluded", "off_excluded"]].sum(axis=1),
            output.total_pa,
        )
        output["weighted_difference"] = output.on_weighted_mean - output.off_weighted_mean
        output.to_csv(out / f"{situation}_player_counts.csv")
        for cutoff in (0, 1000, 2000, 3000):
            sample = output.loc[output.total_pa.ge(cutoff)]
            coverage.append(dict(situation=situation, min_pa=cutoff, players=len(sample),
                                 both_eligible=(sample.on_eligible.gt(0) & sample.off_eligible.gt(0)).sum(),
                                 weighted_differences=sample.weighted_difference.count()))
        print(situation, len(output), "players, eligible PA",
              output.on_eligible.sum() + output.off_eligible.sum(),
              "excluded PA", output.on_excluded.sum() + output.off_excluded.sum())
    pd.DataFrame(coverage).to_csv(out / "coverage.csv", index=False)
    WEIGHTS.rename_axis("outcome").to_csv(out / "fixed_weights.csv", float_format="%.2f")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=RESULTS)
    args = parser.parse_args()
    prepare(args.output_dir)


if __name__ == "__main__":
    main()
