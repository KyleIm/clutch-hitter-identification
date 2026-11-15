"""Compare situational metrics with overall batting production on shared samples."""
import argparse
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import rankdata

from analyze_clutch_regression import BASE, CUTOFFS, ROOT, SEED, plt
from analyze_weighted_benchmark import RAW, WEIGHTED, load_samples

OUT = BASE / "Batting_Performance"
OVERALL = ["overall_hit_rate", "overall_weighted_production", "ops_plus", "wrc_plus"]
SITUATIONAL = ["period_wpa", "period_clutch_estimate", "RISP", "LIPS", "wRISP", "wLIPS"]
RATE = ["wpa_per_600", "clutch_per_600", *RAW]
LABELS = dict(zip([*OVERALL, *SITUATIONAL, *RATE],
                  ["Eligible hit rate", "Weighted production", "OPS+", "wRC+", "WPA", "Clutch",
                   "RISP", "LIPS", "wRISP", "wLIPS", "WPA / 600", "Clutch / 600",
                   "Raw RISP", "Raw LIPS", "Raw wRISP", "Raw wLIPS"]))
COMPARISONS = [(benchmark, score) for benchmark, scores in (
    ("period_wpa", ["RISP", "LIPS"]),
    ("period_clutch_estimate", ["RISP", "LIPS", "wRISP", "wLIPS"]),
) for score in scores]
METHODS = ["pearson", "spearman", "partial_pearson_log_pa"]
DRAWS = 10000


def load_players():
    data, _ = load_samples()
    binomial = pd.read_csv(ROOT / "Results/RISP_LIPS/players.csv").set_index("batter").loc[data.batter]
    counts = pd.read_csv(WEIGHTED / "risp_player_counts.csv").set_index("batter").loc[data.batter]
    np.testing.assert_array_equal(data.total_pa, binomial.total_pa)
    np.testing.assert_array_equal(data.total_pa, counts.total_pa)
    hits = binomial.n_success_risp + binomial.b_success_risp
    trials = binomial.n_trials_risp + binomial.b_trials_risp
    np.testing.assert_array_equal(hits, binomial.n_success_lips + binomial.b_success_lips)
    np.testing.assert_array_equal(trials, binomial.n_trials_lips + binomial.b_trials_lips)
    weights = pd.read_csv(WEIGHTED / "fixed_weights.csv").set_index("outcome").weight
    totals = counts[[f"on_{key}" for key in weights.index]].set_axis(weights.index, axis=1).add(
        counts[[f"off_{key}" for key in weights.index]].set_axis(weights.index, axis=1))
    eligible = totals.sum(axis=1)
    np.testing.assert_array_equal(eligible, counts.on_eligible + counts.off_eligible)
    data["overall_hit_rate"] = hits.div(trials.where(trials.gt(0))).to_numpy()
    data["overall_weighted_production"] = totals.dot(weights).div(eligible.where(eligible.gt(0))).to_numpy()
    data["overall_hit_trials"] = trials.to_numpy()
    data["overall_weighted_trials"] = eligible.to_numpy()
    for source, metric in (("BaseballReference", "ops_plus"), ("FanGraphs", "wrc_plus")):
        index = pd.read_csv(ROOT / "Data" / source / f"{metric}_1998_2025_period.csv")
        merged = data.merge(index, how="outer", on="batter", validate="one_to_one",
                            suffixes=("", "_check"), indicator=True)
        if not merged._merge.eq("both").all():
            raise ValueError(f"Player IDs differ for {metric}")
        if "bbref_id_check" in merged:
            np.testing.assert_array_equal(merged.bbref_id, merged.pop("bbref_id_check"))
        data = merged.drop(columns="_merge")
    data["wpa_per_600"] = 600 * data.period_wpa / data.total_pa
    data["clutch_per_600"] = 600 * data.period_clutch_estimate / data.total_pa
    return data.sort_values("batter")


def correlations(values, method):
    """Calculate same-draw cross-correlations and the two-index consistency check."""
    if method == "spearman":
        values = rankdata(values, axis=1)
    values = values - values.mean(axis=1, keepdims=True)
    if method == "partial_pearson_log_pa":
        log_pa = values[:, :, -1:]
        projection = (values * log_pa).sum(axis=1, keepdims=True) / (log_pa ** 2).sum(axis=1, keepdims=True)
        values = values - projection * log_pa
    values = values[:, :, :-1]
    values /= np.sqrt((values ** 2).sum(axis=1, keepdims=True))
    overall, situational = values[:, :, :len(OVERALL)], values[:, :, len(OVERALL):]
    cross = situational.transpose(0, 2, 1) @ overall
    return cross, (overall[:, :, 2] * overall[:, :, 3]).sum(axis=1)


def intervals(values, rng):
    observed = {method: correlations(values[None], method) for method in METHODS}
    samples = {method: [] for method in METHODS}
    checks = {method: [] for method in METHODS}
    for start in range(0, DRAWS, 128):
        ids = rng.integers(len(values), size=(min(128, DRAWS - start), len(values)))
        for method in METHODS:
            block, check = correlations(values[ids], method)
            samples[method].append(block)
            checks[method].append(check)
    return (observed, {key: np.concatenate(batches) for key, batches in samples.items()},
            {key: np.concatenate(batches) for key, batches in checks.items()})


def run(data):
    results, contrasts, coverage = [], [], []
    rng = np.random.default_rng(SEED)
    for cutoff in CUTOFFS:
        candidate = data[data.total_pa.ge(cutoff)]
        assert len(candidate) == CUTOFFS[cutoff]
        columns = [*OVERALL, *SITUATIONAL, *RATE]
        complete = np.isfinite(candidate[columns]).all(axis=1)
        sample = candidate.loc[complete]
        for metric in OVERALL:
            diagnostic = {k: int(candidate[k].fillna(0).gt(0).sum()) for k in
                          [f"{metric}_{x}" for x in ("missing_rows", "missing_metric_seasons",
                                                     "extra_positive_pa_seasons")] if k in candidate}
            pa = candidate.get(f"{metric}_pa_difference", pd.Series(dtype=float)).dropna()
            coverage.append(dict(min_pa=cutoff, metric=metric, candidates=len(candidate),
                                 complete_cases=len(sample), missing=int(candidate[metric].isna().sum()),
                                 source_pa_available=len(pa), pa_discrepancies=int(pa.ne(0).sum()),
                                 pa_delta_min=pa.min(), pa_delta_max=pa.max(), **diagnostic))
        values = np.column_stack((sample[columns], np.log(sample.total_pa)))
        observed, draws, checks = intervals(values, rng)
        for method, (matrix, consistency) in observed.items():
            band_low, band_high = np.quantile(draws[method], [.025, .975], axis=0)
            for i, situation in enumerate([*SITUATIONAL, *RATE]):
                for j, overall in enumerate(OVERALL):
                    results.append(dict(min_pa=cutoff, method=method, situational=situation, overall=overall,
                                        n=len(sample), r=matrix[0, i, j], ci_low=band_low[i, j],
                                        ci_high=band_high[i, j], replicates=DRAWS))
            lo, hi = np.quantile(checks[method], [.025, .975])
            results.append(dict(min_pa=cutoff, method=method, situational="ops_plus", overall="wrc_plus",
                                n=len(sample), r=consistency[0], ci_low=lo, ci_high=hi, replicates=DRAWS))
            for benchmark, score in COMPARISONS:
                b, s = (SITUATIONAL.index(k) for k in (benchmark, score))
                diff = abs(draws[method][:, b]) - abs(draws[method][:, s])
                low, high = np.quantile(diff, [.025, .975], axis=0)
                primary = cutoff == 2000 and method == "pearson" and benchmark == "period_clutch_estimate"
                adjusted = np.quantile(diff, [.025 / 16, 1 - .025 / 16], axis=0) if primary else np.full((2, 4), np.nan)
                for j, overall in enumerate(OVERALL):
                    contrasts.append(dict(min_pa=cutoff, method=method, benchmark=benchmark, score=score,
                                          overall=overall, n=len(sample), primary=primary, replicates=DRAWS,
                                          delta=abs(matrix[0, b, j])-abs(matrix[0, s, j]),
                                          ci_low=low[j], ci_high=high[j],
                                          adjusted_ci_low=adjusted[0, j], adjusted_ci_high=adjusted[1, j]))
    return pd.DataFrame(results), pd.DataFrame(contrasts), pd.DataFrame(coverage)


def plot(data, results, out):
    out.mkdir(parents=True, exist_ok=True)

    def save(fig, name):
        fig.savefig(out / f"{name}.png", dpi=175)
        plt.close(fig)

    primary = results.query("min_pa == 2000 and situational in @SITUATIONAL")
    for method in METHODS[:2]:
        table = primary[primary.method.eq(method)].pivot(index="situational", columns="overall", values="r").loc[SITUATIONAL, OVERALL]
        fig, ax = plt.subplots(figsize=(8, 4), layout="constrained")
        image = ax.imshow(table, cmap="RdBu_r", vmin=-1, vmax=1)
        ax.set(xticks=range(4), yticks=range(6), xticklabels=[LABELS[k] for k in OVERALL],
               yticklabels=[LABELS[k] for k in SITUATIONAL], title=f"{method.title()} correlations | PA ≥ 2,000")
        for i, row in enumerate(table.to_numpy()):
            for j, value in enumerate(row):
                ax.text(j, i, f"{value:.2f}", ha="center", va="center", color="white" if abs(value) > .65 else "black")
        fig.colorbar(image, ax=ax)
        save(fig, f"{method}_heatmap")

    sample = data[data.total_pa.ge(2000)].dropna(subset=[*OVERALL, *SITUATIONAL, *RATE])
    fig, axes = plt.subplots(4, 2, figsize=(8, 10), layout="constrained")
    for row, y in enumerate(SITUATIONAL[:4]):
        for col, x in enumerate(OVERALL[2:]):
            ax = axes[row, col]
            ax.scatter(sample[x], sample[y], s=8, alpha=.35, color="#31768b")
            ax.set(xlabel=LABELS[x], ylabel=LABELS[y])
    save(fig, "index_scatter")

    for method_list, name in ((METHODS[:1], "correlation_intervals"),
                              ([METHODS[0], METHODS[2]], "before_after_pa_control")):
        fig, axes = plt.subplots(2, 2, figsize=(9, 6), sharex=True, layout="constrained")
        for ax, overall in zip(axes.flat, OVERALL):
            for method, offset, color in zip(method_list, [0, .18], ["#31768b", "#a8522c"]):
                frame = primary.query("overall == @overall and method == @method").set_index("situational").loc[SITUATIONAL]
                ax.errorbar(frame.r, np.arange(6) + offset,
                            xerr=[frame.r-frame.ci_low, frame.ci_high-frame.r], fmt="o", capsize=2, color=color,
                            label="Raw" if method == "pearson" else "Control log(PA)")
            ax.set(title=LABELS[overall], yticks=range(6), yticklabels=[LABELS[k] for k in SITUATIONAL])
            ax.axvline(0, color=".65", linewidth=.8)
        axes[0, 0].legend(fontsize=8)
        fig.supxlabel("Pearson correlation and nominal 95% interval")
        save(fig, name)

    fig, axes = plt.subplots(2, 2, figsize=(9, 6), sharex=True, sharey=True, layout="constrained")
    for ax, overall in zip(axes.flat, OVERALL):
        for item in SITUATIONAL:
            frame = results.query("overall == @overall and method == 'pearson' and situational == @item")
            ax.plot(frame.min_pa, frame.r, marker="o", label=LABELS[item])
        ax.set(title=LABELS[overall], xticks=list(CUTOFFS))
        ax.axhline(0, color=".65", linewidth=.8)
    axes[0, 0].legend(fontsize=8, ncol=2)
    fig.supxlabel("Minimum Retrosheet PA")
    fig.supylabel("Pearson correlation")
    save(fig, "cutoff_sensitivity")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=OUT)
    out = parser.parse_args().output_dir
    data = load_players()
    results, contrasts, coverage = run(data)
    out.mkdir(parents=True, exist_ok=True)
    coverage.to_csv(out / "coverage.csv", index=False)
    data.to_csv(out / "players.csv", index=False)
    results.to_csv(out / "correlations.csv", index=False)
    contrasts.to_csv(out / "bootstrap_comparisons.csv", index=False)
    plot(data, results, out / "figures")
    print(coverage.to_string(index=False))


if __name__ == "__main__":
    main()
