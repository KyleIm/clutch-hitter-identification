#!/usr/bin/env python3
import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


TITLE_FONT_SIZE = 25
LABEL_FONT_SIZE = 20
TICK_FONT_SIZE = 20
LEGEND_FONT_SIZE = 16


def build_histogram(input_path, min_pa, bins):
    df = pd.read_csv(input_path)
    filtered = df[df["total_pa"] >= min_pa].dropna(subset=["S"]).copy()
    if filtered.empty:
        raise ValueError(f"No rows found with total_pa >= {min_pa} and valid S.")

    s_values = filtered["S"]
    mean_s = s_values.mean()
    median_s = s_values.median()
    std_s = s_values.std()

    fig, ax = plt.subplots(figsize=(12, 8))
    ax.hist(
        s_values,
        bins=bins,
        edgecolor="black",
        linewidth=1.0,
        alpha=0.78,
        color="#4C78A8",
    )
    ax.axvline(
        mean_s,
        color="#E45756",
        linewidth=2.2,
        label=f"mean = {mean_s:.3f}",
    )
    ax.axvline(
        median_s,
        color="#54A24B",
        linewidth=2.2,
        linestyle="--",
        label=f"median = {median_s:.3f}",
    )
    ax.set_xlabel("Binomial ON/OFF S", fontsize=LABEL_FONT_SIZE)
    ax.set_ylabel("Players", fontsize=LABEL_FONT_SIZE)
    ax.set_title(
        f"2025 MLB Binomial ON/OFF S Distribution\n"
        f"PA >= {min_pa}, N={len(filtered)}, std={std_s:.3f}",
        fontsize=TITLE_FONT_SIZE,
        pad=16,
    )
    ax.tick_params(axis="both", labelsize=TICK_FONT_SIZE)
    ax.legend(fontsize=LEGEND_FONT_SIZE)
    fig.tight_layout()

    return fig, {
        "input": input_path,
        "players": len(filtered),
        "mean": mean_s,
        "median": median_s,
        "std": std_s,
    }


def main():
    base_dir = Path(__file__).resolve().parents[1]
    default_input = base_dir / "Data" / "mlb_2025_RISP_sample_counts.csv"

    parser = argparse.ArgumentParser(description="Plot a histogram of RISP S values.")
    parser.add_argument("--input", default=default_input, type=Path)
    parser.add_argument("--min-pa", default=251, type=int)
    parser.add_argument("--bins", default=30, type=int)
    args = parser.parse_args()

    _, stats = build_histogram(args.input, args.min_pa, args.bins)
    plt.show()

    print(f"input: {stats['input']}")
    print(f"players: {stats['players']}")
    print(f"S_mean: {stats['mean']:.6f}")
    print(f"S_median: {stats['median']:.6f}")
    print(f"S_std: {stats['std']:.6f}")


if __name__ == "__main__":
    main()
