#!/usr/bin/env python3
import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


def main():
    base_dir = Path(__file__).resolve().parents[1]
    default_input = base_dir / "Data" / "mlb_2025_RISP_sample_counts.csv"

    parser = argparse.ArgumentParser(description="Plot a histogram of RISP S values.")
    parser.add_argument("--input", default=default_input, type=Path)
    parser.add_argument("--min-pa", default=251, type=int)
    parser.add_argument("--bins", default=30, type=int)
    parser.add_argument(
        "--output",
        type=Path,
        help="Optional path for saving the histogram image.",
    )
    args = parser.parse_args()

    df = pd.read_csv(args.input)
    filtered = df[df["total_pa"] >= args.min_pa].dropna(subset=["S"]).copy()
    if filtered.empty:
        raise ValueError(f"No rows found with total_pa >= {args.min_pa} and valid S.")

    s_values = filtered["S"]
    mean_s = s_values.mean()
    median_s = s_values.median()
    std_s = s_values.std()

    plt.figure(figsize=(11, 7))
    plt.hist(
        s_values,
        bins=args.bins,
        edgecolor="black",
        linewidth=1.0,
        alpha=0.78,
        color="#4C78A8",
    )
    plt.axvline(mean_s, color="#E45756", linewidth=2.2, label=f"mean = {mean_s:.3f}")
    plt.axvline(
        median_s,
        color="#54A24B",
        linewidth=2.2,
        linestyle="--",
        label=f"median = {median_s:.3f}",
    )
    plt.xlabel("RISP Li-Ma S")
    plt.ylabel("Players")
    plt.title(
        f"2025 MLB RISP S Distribution (PA >= {args.min_pa}, N={len(filtered)}, "
        f"std={std_s:.3f})"
    )
    plt.legend()
    plt.tight_layout()
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(args.output, dpi=160)
    else:
        plt.show()

    print(f"input: {args.input}")
    if args.output:
        print(f"output: {args.output}")
    print(f"players: {len(filtered)}")
    print(f"S_mean: {mean_s:.6f}")
    print(f"S_median: {median_s:.6f}")
    print(f"S_std: {std_s:.6f}")


if __name__ == "__main__":
    main()
