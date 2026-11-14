"""Reproduce the 1998–2025 RISP–LIPS portfolio analysis."""
import argparse
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats

from lima_histogram_RISP_sample import (
    add_event_result, add_situation_flag, binomial_on_off_s,
)

ROOT = Path(__file__).resolve().parents[1]
CATEGORIES = ("neither", "risp_only", "lips_only", "both")
SITUATIONS = ("risp", "lips")
CUTOFFS = (1000, 2000, 3000)
SEED = 20251113
RUNNER_COLUMN = "runner_situation_before_final_pitch"
PA_COLUMNS = [
    "game_date", "batter", "inning", "bat_score", "fld_score", "events",
    "runner_situation_start", RUNNER_COLUMN,
]
METRICS = {
    "score": "Signed binomial likelihood-ratio score (S)",
    "rate_difference": "ON − OFF hit rate (percentage points)",
}
METHODS = ("pearson", "spearman")
MISSING_PA = ("events", "inning", "bat_score", "fld_score", "batter")


def count_categories(pa):
    if pa[list(MISSING_PA)].isna().any().any():
        raise ValueError("Missing event, game-state, or hitter information")
    risp, lips = [add_situation_flag(pa, s, RUNNER_COLUMN)["is_risp"] for s in SITUATIONS]
    category = risp.astype(int) + 2 * lips.astype(int)
    result = add_event_result(pa[["events"]])["event_result"]
    counts = pd.DataFrame({
        "batter": pa["batter"], "category": category, "pa": 1,
        "hits": result.eq("success").astype(int),
        "trials": result.ne("excluded").astype(int),
    }).groupby(["batter", "category"])[["pa", "hits", "trials"]].sum()
    counts = counts.unstack(fill_value=0).reindex(
        columns=pd.MultiIndex.from_product([["pa", "hits", "trials"], range(4)]),
        fill_value=0,
    )
    if counts["pa"].to_numpy().sum() != len(pa) or (
        counts["trials"].to_numpy().sum() != result.ne("excluded").sum()
    ):
        raise ValueError("Four-category counts do not cover the input")
    counts.columns = [f"{CATEGORIES[i]}_{measure}" for measure, i in counts.columns]
    return counts


def margins(counts):
    """Project the last axis onto RISP and LIPS, each ordered ON, OFF."""
    a, b, c, d = np.moveaxis(counts, -1, 0)
    return np.stack([b + d, a + c], axis=-1), np.stack([c + d, a + b], axis=-1)


def load_inputs(data_dir):
    summaries = []
    for situation in SITUATIONS:
        source = data_dir / f"mlb_1998_2025_{situation.upper()}_sample_counts.csv"
        summary = pd.read_csv(source)
        if summary.batter.isna().any() or summary.batter.duplicated().any():
            raise ValueError(f"Missing or duplicate player ID in {source}")
        summaries.append(summary.set_index("batter").add_suffix(f"_{situation}"))

    merged = summaries[0].join(summaries[1], how="outer", validate="one_to_one")
    if not merged.total_pa_risp.eq(merged.total_pa_lips).all():
        raise ValueError("RISP and LIPS player IDs or total PA do not match")
    merged["total_pa"] = merged.total_pa_risp
    merged["player_name"] = merged.player_name_risp

    seasonal = []
    for year in range(1998, 2026):
        source = data_dir / "Retrosheet" / "Compact" / f"mlb_{year}_plate_appearances_compact.csv"
        pa = pd.read_csv(source, usecols=PA_COLUMNS)
        if pa.empty or not pa.game_date.str.startswith(f"{year}-", na=False).all():
            raise ValueError(f"Unexpected date coverage in {source}")
        seasonal.append(count_categories(pa))
    four = pd.concat(seasonal).groupby(level="batter").sum()
    if not four.index.equals(merged.sort_index().index):
        raise ValueError("Compact inputs and marginal summaries have different player IDs")
    return merged.sort_index(), four


def verify_margins(merged, four):
    for (measure, on_field, off_field) in (
        ("pa", "n", "b"), ("hits", "n_success", "b_success"),
        ("trials", "n_trials", "b_trials"),
    ):
        for s, actual in zip(SITUATIONS, margins(four[[f"{c}_{measure}" for c in CATEGORIES]].to_numpy())):
            np.testing.assert_array_equal(actual, merged[[f"{on_field}_{s}", f"{off_field}_{s}"]])
    audit = []
    for s in SITUATIONS:
        on, off = [merged[f"{prefix}_trials_{s}"].to_numpy() for prefix in ("n", "b")]
        h_on, h_off = [merged[f"{prefix}_success_{s}"].to_numpy() for prefix in ("n", "b")]
        for prefix, hits, trials in (("n", h_on, on), ("b", h_off, off)):
            np.testing.assert_array_equal(
                merged[f"{prefix}_failure_{s}"], trials - hits,
            )
            np.testing.assert_array_equal(
                merged[f"{prefix}_excluded_{s}"], merged[f"{prefix}_{s}"] - trials,
            )
            with np.errstate(divide="ignore", invalid="ignore"):
                np.testing.assert_allclose(merged[f"{prefix}_rate_{s}"], hits / trials, atol=1e-12)
        observed = merged[f"S_{s}"].to_numpy()
        expected = binomial_on_off_s(h_on, on - h_on, h_off, off - h_off)
        np.testing.assert_allclose(observed, expected, atol=1e-7, rtol=0)
        valid = np.isfinite(observed)
        tables = np.stack([h_on, on - h_on, h_off, off - h_off], axis=-1)[valid].reshape(-1, 2, 2)
        cells = tables.sum(axis=1, keepdims=True) * tables.sum(axis=2, keepdims=True)
        cells = cells / tables.sum(axis=(1, 2), keepdims=True)
        with np.errstate(divide="ignore", invalid="ignore"):
            g = 2 * np.where(tables > 0, tables * np.log(tables / cells), 0).sum(axis=(1, 2))
        np.testing.assert_allclose(observed[valid] ** 2, g, atol=1e-10, rtol=0)
        np.testing.assert_array_equal(np.sign(observed[valid]), np.sign((h_on * off - h_off * on)[valid]))
        merged[f"score_{s}"] = observed
        merged[f"rate_difference_{s}"] = merged[f"n_rate_{s}"] - merged[f"b_rate_{s}"]
        audit.append({
            "situation": s, "players": len(merged), "valid_scores": int(valid.sum()),
            "missing_scores": int(np.isnan(observed).sum()), "infinite_scores": int(np.isinf(observed).sum()),
            "eligible_trials": int((on + off).sum()), "max_abs_g_error": np.max(np.abs(observed[valid] ** 2 - g)),
            "pooled_on_rate": h_on.sum() / on.sum(), "pooled_off_rate": h_off.sum() / off.sum(),
        })
    return pd.DataFrame(audit)


def row_correlation(x, y):
    x = x - x.mean(axis=-1, keepdims=True)
    y = y - y.mean(axis=-1, keepdims=True)
    denominator = np.sqrt((x * x).sum(axis=-1) * (y * y).sum(axis=-1))
    return np.clip(np.divide((x * y).sum(axis=-1), denominator,
                            out=np.full(denominator.shape, np.nan),
                            where=denominator > 0), -1, 1)


def simulate_null(hits, trials, masks, simulations, seed):
    rng = np.random.default_rng(seed)
    pooled_rate = hits.sum(axis=1) / trials.sum(axis=1)
    trial_margins = margins(trials)
    output = {cutoff: np.empty((simulations, 2)) for cutoff in masks}
    for start in range(0, simulations, 256):
        stop = min(start + 256, simulations)
        draws = rng.binomial(trials, pooled_rate[:, None], (stop - start, *trials.shape))
        scores = []
        for successes, counts in zip(margins(draws), trial_margins):
            failures = counts - successes
            scores.append(binomial_on_off_s(
                successes[..., 0], failures[..., 0], successes[..., 1], failures[..., 1],
            ))
        for cutoff, mask in masks.items():
            x, y = (score[:, mask] for score in scores)
            output[cutoff][start:stop, 0] = row_correlation(x, y)
            output[cutoff][start:stop, 1] = row_correlation(
                stats.rankdata(x, axis=1), stats.rankdata(y, axis=1),
            )
    return output


def correlations(x, y, rng):
    pearson = stats.pearsonr(x, y)
    spearman = stats.spearmanr(x, y)
    interval = pearson.confidence_interval()
    rank_bootstrap = []
    for _ in range(10):
        indices = rng.integers(len(x), size=(200, len(x)))
        rank_bootstrap.extend(row_correlation(
            stats.rankdata(x[indices], axis=1), stats.rankdata(y[indices], axis=1),
        ))
    low, high = np.nanquantile(rank_bootstrap, [0.025, 0.975])
    return [(pearson.statistic, pearson.pvalue, interval.low, interval.high),
            (spearman.statistic, spearman.pvalue, low, high)]


def overlaps_and_extremes(sample, columns, cutoff, metric):
    size = int(np.ceil(0.05 * len(sample)))
    overlap = {}
    extremes = []
    for tail, ascending in (("top", False), ("bottom", True)):
        groups = []
        for s, col in zip(SITUATIONS, columns):
            ranked = sample.sort_values([col, "batter"], ascending=[ascending, True])
            groups.append(set(ranked.index[:size]))
            for batter, row in ranked.head(5).iterrows():
                extremes.append({
                    "min_pa": cutoff, "metric": metric, "selection": f"{s}_{tail}",
                    "batter": batter, "player_name": row.player_name,
                    "risp": row[columns[0]], "lips": row[columns[1]],
                })
        overlap[tail] = len(groups[0] & groups[1])
    if metric == "score":
        gaps = sample[columns[0]] - sample[columns[1]]
        for label, ascending in (("risp_higher", False), ("lips_higher", True)):
            selection = sample.assign(gap=gaps).sort_values(
                ["gap", "batter"], ascending=[ascending, True],
            ).head(5)
            for batter, row in selection.iterrows():
                extremes.append({
                    "min_pa": cutoff, "metric": metric, "selection": label,
                    "batter": batter, "player_name": row.player_name,
                    "risp": row[columns[0]], "lips": row[columns[1]],
                })
    return size, overlap, extremes


def plot_results(samples, null, results, figure_dir):
    fig, axes = plt.subplots(2, 3, figsize=(13, 7), layout="constrained")
    for col, (cutoff, sample) in enumerate(samples.items()):
        for row, metric in enumerate(METRICS):
            ax = axes[row, col]
            scale = 100 if metric == "rate_difference" else 1
            ax.scatter(scale * sample[f"{metric}_risp"], scale * sample[f"{metric}_lips"],
                       s=12, alpha=0.45, color="#266A83", linewidths=0)
            ax.axhline(0, color=".65", lw=0.7)
            ax.axvline(0, color=".65", lw=0.7)
            pair = results[(results.min_pa == cutoff) & (results.metric == metric)]
            r, rho = pair.coefficient
            ax.set(title=f"≥ {cutoff:,} PA · n = {len(sample):,}\nr = {r:.3f} · ρ = {rho:.3f}",
                   xlabel=f"RISP {METRICS[metric]}", ylabel=f"LIPS {METRICS[metric]}")
    fig.savefig(figure_dir / "scatter.png", dpi=200)
    plt.close(fig)

    fig, axes = plt.subplots(1, 3, figsize=(11, 4), sharey=True, layout="constrained")
    for ax, (cutoff, sample) in zip(axes, samples.items()):
        artists = ax.boxplot([sample.score_risp, sample.score_lips], patch_artist=True)
        for box, color in zip(artists["boxes"], ("#A1CFDF", "#F1B58C")):
            box.set_facecolor(color)
        ax.set(xticks=[1, 2], xticklabels=["RISP", "LIPS"],
               title=f"≥ {cutoff:,} PA · n = {len(sample):,}")
        ax.axhline(0, color=".65", lw=0.7)
    axes[0].set_ylabel(METRICS["score"])
    fig.savefig(figure_dir / "boxplot.png", dpi=200)
    plt.close(fig)

    fig, axes = plt.subplots(2, 3, figsize=(12, 6), layout="constrained")
    for col, cutoff in enumerate(samples):
        for row, method in enumerate(METHODS):
            ax = axes[row, col]
            observed = results.loc[(results.min_pa == cutoff) & (results.metric == "score")
                                   & (results.method == method), "coefficient"].iloc[0]
            ax.hist(null[cutoff][:, row], bins=35, color="#266A83")
            ax.axvline(observed, color="#B84926", lw=2, label=f"Observed {observed:.3f}")
            ax.set(title=f"≥ {cutoff:,} PA", xlabel=f"{method.title()} correlation")
            if col == 0:
                ax.set_ylabel("Simulations")
            ax.legend(frameon=False)
    fig.savefig(figure_dir / "null_correlations.png", dpi=200)
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=ROOT / "Data")
    parser.add_argument("--output-dir", type=Path, default=ROOT / "Results" / "RISP_LIPS")
    parser.add_argument("--simulations", type=int, default=10000)
    parser.add_argument("--seed", type=int, default=SEED)
    args = parser.parse_args()
    if args.simulations < 1 or args.seed < 0:
        parser.error("expected a positive simulation count and a nonnegative seed")

    merged, four = load_inputs(args.data_dir)
    audit = verify_margins(merged, four)
    metric_columns = [f"{metric}_{s}" for metric in METRICS for s in SITUATIONS]
    valid = np.isfinite(merged[metric_columns]).all(axis=1)
    merged["valid_pair"] = valid
    samples = {cutoff: merged.loc[valid & (merged.total_pa >= cutoff)] for cutoff in CUTOFFS}
    coverage = pd.DataFrame([
        {"min_pa": cutoff, "matched_players": int((merged.total_pa >= cutoff).sum()),
         "valid_pairs": len(sample), "excluded_invalid_pairs": int((merged.total_pa >= cutoff).sum()) - len(sample)}
        for cutoff, sample in [(0, merged.loc[valid]), *samples.items()]
    ])
    analysis = four.loc[samples[CUTOFFS[0]].index]
    trials = analysis[[f"{c}_trials" for c in CATEGORIES]].to_numpy()
    hits = analysis[[f"{c}_hits" for c in CATEGORIES]].to_numpy()
    masks = {cutoff: analysis.index.isin(sample.index) for cutoff, sample in samples.items()}
    null = simulate_null(hits, trials, masks, args.simulations, args.seed)

    rng = np.random.default_rng(args.seed)
    correlations_table, descriptives, extremes, tail_overlap, null_summary = [], [], [], [], []
    for cutoff, sample in samples.items():
        for metric in METRICS:
            columns = [f"{metric}_{s}" for s in SITUATIONS]
            for s, column in zip(SITUATIONS, columns):
                series = sample[column]
                descriptives.append({
                    "min_pa": cutoff, "metric": metric, "situation": s, "n": len(series),
                    "mean": series.mean(), "median": series.median(), "std": series.std(),
                    "q1": series.quantile(0.25), "q3": series.quantile(0.75), "skewness": series.skew(),
                })
            size, overlap, selected = overlaps_and_extremes(sample, columns, cutoff, metric)
            extremes.extend(selected)
            for tail, count in overlap.items():
                tail_overlap.append({
                    "min_pa": cutoff, "metric": metric, "tail": tail, "n": len(sample),
                    "players_per_tail": size, "overlap": count, "overlap_fraction": count / size,
                })
            estimates = correlations(*(sample[c].to_numpy() for c in columns), rng)
            for index, (method, estimate) in enumerate(zip(METHODS, estimates)):
                observed, p, low, high = estimate
                correlations_table.append({
                    "min_pa": cutoff, "metric": metric, "method": method, "n": len(sample),
                    "coefficient": observed, "p_against_zero": p, "ci_low": low, "ci_high": high,
                })
                if metric == "score":
                    draws = null[cutoff][:, index]
                    if not np.isfinite(draws).all():
                        raise ValueError("Undefined correlation in Monte Carlo draws")
                    q_low, q_high = np.quantile(draws, [0.025, 0.975])
                    null_summary.append({
                        "min_pa": cutoff, "method": method, "n": len(sample), "observed": observed,
                        "null_mean": draws.mean(), "null_q025": q_low, "null_q975": q_high,
                        "excess": observed - draws.mean(),
                        "p_positive_excess": (1 + (draws >= observed).sum()) / (args.simulations + 1),
                        "simulations": args.simulations, "seed": args.seed,
                    })

    results = pd.DataFrame(correlations_table)
    summary = pd.DataFrame(null_summary)
    figure_dir = args.output_dir / "figures"
    figure_dir.mkdir(parents=True, exist_ok=True)
    tables = {
        "players": merged.reset_index(),
        "four_category_counts": four.reset_index(),
        "integrity": audit,
        "sample_coverage": coverage,
        "descriptive_statistics": pd.DataFrame(descriptives),
        "correlations": results,
        "tail_overlap": pd.DataFrame(tail_overlap),
        "extremes": pd.DataFrame(extremes),
        "null_summary": summary,
    }
    for name, frame in tables.items():
        frame.to_csv(args.output_dir / f"{name}.csv", index=False)
    plot_results(samples, null, results, figure_dir)
    print(coverage.to_string(index=False))
    print(summary.to_string(index=False))


if __name__ == "__main__":
    main()
