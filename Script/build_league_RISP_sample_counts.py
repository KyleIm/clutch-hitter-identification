#!/usr/bin/env python3
import argparse
from pathlib import Path

import pandas as pd

from lima_histogram_RISP_sample import (
    add_event_result,
    add_risp_flag,
    li_ma_s,
    success_rate,
)


OUTPUT_COLUMNS = [
    "player_name",
    "batter",
    "teams",
    "n",
    "b",
    "alpha",
    "n_success",
    "n_failure",
    "n_excluded",
    "n_rate",
    "b_success",
    "b_failure",
    "b_excluded",
    "b_rate",
    "S",
    "total_pa",
]


def build_league_counts(df):
    rows = []
    for (batter, player_name), player_df in df.groupby(
        ["batter", "player_name"], dropna=False
    ):
        risp_df = player_df[player_df["is_risp"]]
        non_risp_df = player_df[~player_df["is_risp"]]

        n_success = int((risp_df["event_result"] == "success").sum())
        n_failure = int((risp_df["event_result"] == "failure").sum())
        n_excluded = int((risp_df["event_result"] == "excluded").sum())
        b_success = int((non_risp_df["event_result"] == "success").sum())
        b_failure = int((non_risp_df["event_result"] == "failure").sum())
        b_excluded = int((non_risp_df["event_result"] == "excluded").sum())
        n = int(len(risp_df))
        b = int(len(non_risp_df))
        alpha = n / b if b else float("nan")
        n_rate = success_rate(n_success, n_failure)
        b_rate = success_rate(b_success, b_failure)

        rows.append(
            {
                "player_name": player_name,
                "batter": batter,
                "teams": "+".join(sorted(player_df["team"].dropna().unique())),
                "n": n,
                "b": b,
                "alpha": alpha,
                "n_success": n_success,
                "n_failure": n_failure,
                "n_excluded": n_excluded,
                "n_rate": n_rate,
                "b_success": b_success,
                "b_failure": b_failure,
                "b_excluded": b_excluded,
                "b_rate": b_rate,
                "S": li_ma_s(n_rate, b_rate, alpha),
                "total_pa": int(len(player_df)),
            }
        )

    return pd.DataFrame(rows)[OUTPUT_COLUMNS].sort_values(
        ["player_name", "batter"]
    )


def main():
    base_dir = Path(__file__).resolve().parents[1]
    default_input_dir = base_dir / "Data" / "Retrosheet" / "2025"
    default_output = base_dir / "Data" / "mlb_2025_RISP_sample_counts.csv"

    parser = argparse.ArgumentParser(
        description="Build league-wide RISP sample counts by player."
    )
    parser.add_argument("--input-dir", default=default_input_dir, type=Path)
    parser.add_argument("--output", default=default_output, type=Path)
    parser.add_argument(
        "--situation-column",
        default="runner_situation_before_final_pitch",
        choices=["runner_situation_start", "runner_situation_before_final_pitch"],
    )
    args = parser.parse_args()

    files = sorted(args.input_dir.glob("*_2025_plate_appearances_compact.csv"))
    if not files:
        raise FileNotFoundError(f"No compact CSV files found in {args.input_dir}")

    df = pd.concat((pd.read_csv(path) for path in files), ignore_index=True)
    df = add_risp_flag(df, args.situation_column)
    df = add_event_result(df)
    counts = build_league_counts(df)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    counts.to_csv(args.output, index=False)

    valid = counts.dropna(subset=["S"]).copy()
    median_s = valid["S"].median()
    median_row = valid.iloc[(valid["S"] - median_s).abs().argsort().iloc[0]]
    min_row = valid.loc[valid["S"].idxmin()]
    max_row = valid.loc[valid["S"].idxmax()]

    print(f"input_dir: {args.input_dir}")
    print(f"output: {args.output}")
    print(f"teams/files: {len(files)}")
    print(f"players: {len(counts)}")
    print(f"valid_S_players: {len(valid)}")
    print()
    print(
        "min_S: "
        f"{min_row['player_name']} ({min_row['batter']}), "
        f"teams={min_row['teams']}, S={min_row['S']:.6f}"
    )
    print(
        "median_S_nearest: "
        f"{median_row['player_name']} ({median_row['batter']}), "
        f"teams={median_row['teams']}, S={median_row['S']:.6f}"
    )
    print(
        "max_S: "
        f"{max_row['player_name']} ({max_row['batter']}), "
        f"teams={max_row['teams']}, S={max_row['S']:.6f}"
    )
    print(f"S_mean: {valid['S'].mean():.6f}")
    print(f"S_std: {valid['S'].std():.6f}")


if __name__ == "__main__":
    main()
