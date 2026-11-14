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
ELIGIBLE = [outcome for outcome in OUTCOMES if outcome != "excluded"]


def classify(events):
    labels = events.map(EVENTS)
    if labels.isna().any():
        raise ValueError(f"Unmapped events: {events[labels.isna()].unique().tolist()}")
    return labels


def load_weights(path):
    """Accept a documented representative row or apply equal league-season weights."""
    frame = pd.read_csv(path)
    if frame.source_url.isna().any() or not frame.source_url.str.startswith("https://").all():
        raise ValueError("Each weight row needs a source URL")
    expected = {(year, league) for year in range(1998, 2026) for league in ("AL", "NL")}
    fixed = len(frame) == 1 and frame.kind.eq("representative_1998_2025").all()
    if not fixed and (
        not frame.kind.eq("league_season").all()
        or len(frame) != len(expected)
        or set(zip(frame.season, frame.league)) != expected
    ):
        raise ValueError("Supply one documented representative row or all 56 AL/NL league-seasons")
    numeric = frame[ELIGIBLE].apply(pd.to_numeric)
    if not np.isfinite(numeric).all().all() or not numeric.zero.eq(0).all():
        raise ValueError("Weights must be finite and zero outcomes must have weight zero")
    if not numeric.drop(columns="zero").gt(0).all().all():
        raise ValueError("Production weights must be positive")
    return numeric.mean()


def prepare(out, weights_path):
    out.mkdir(parents=True, exist_ok=True)
    if weights_path is None and (out / "fixed_weights.csv").exists():
        raise ValueError("Use a fresh output directory for a run without weights")
    weights = load_weights(weights_path) if weights_path else None
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
            output[f"{side}_weighted_mean"] = (
                side_counts[ELIGIBLE].dot(weights).div(eligible.where(eligible.gt(0)))
                if weights is not None else np.nan
            )
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
    if weights is not None:
        weights.rename_axis("outcome").rename("weight").to_csv(out / "fixed_weights.csv")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=RESULTS)
    parser.add_argument("--weights", type=Path, help="Documented coefficient CSV")
    args = parser.parse_args()
    prepare(args.output_dir, args.weights)


if __name__ == "__main__":
    main()
