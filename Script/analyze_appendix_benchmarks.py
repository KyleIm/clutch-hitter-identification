"""Compare unadjusted Ruane BPS and raw differences with ON/OFF scores."""
import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from analyze_clutch_regression import ROOT, SEED, cross_validate, fit_ols, metrics, plt
from analyze_weighted_benchmark import MODELS as PRIOR_MODELS, TARGET, WEIGHTED, load_samples
from prepare_weighted_on_off import WEIGHTS

HITS = ["single", "double", "triple", "home_run"]
RAW_HITS = ["rate_difference_risp", "rate_difference_lips"]
RAW_WEIGHTED = ["weighted_difference_risp", "weighted_difference_lips"]
MODELS = {
    "A1": ["ruane_bps_difference"],
    "A2": RAW_HITS[:1],
    "A3": RAW_HITS[1:],
    "A4": RAW_HITS,
    "A5": RAW_WEIGHTED[:1],
    "A6": RAW_WEIGHTED[1:],
    "A7": RAW_WEIGHTED,
    **PRIOR_MODELS,
}
COMPARISONS = [("A1", "B1"), ("A1", "W1"), ("A4", "B3"), ("A7", "W3")]
REPLICATES = 10000


def player_metrics(players):
    """Rebuild raw rates from counts and check them against prior analyses."""
    prior = pd.read_csv(ROOT / "Results/RISP_LIPS/players.csv").set_index("batter").loc[players.index]
    weights = pd.read_csv(WEIGHTED / "fixed_weights.csv").set_index("outcome").weight
    pd.testing.assert_series_equal(weights, WEIGHTS.rename_axis("outcome"))
    for situation in ("risp", "lips"):
        counts = pd.read_csv(WEIGHTED / f"{situation}_player_counts.csv").set_index("batter")
        if not counts.index.is_unique or set(counts.index) != set(players.index):
            raise ValueError(f"Unexpected {situation} player IDs")
        counts = counts.loc[players.index]
        np.testing.assert_array_equal(counts.total_pa, players.total_pa)
        hit_rates, weighted_rates = {}, {}
        for side, prefix in (("on", "n"), ("off", "b")):
            outcomes = counts[[f"{side}_{name}" for name in weights.index]].set_axis(weights.index, axis=1)
            eligible = outcomes.sum(axis=1)
            trials = outcomes[["zero", *HITS]].sum(axis=1)
            hits = outcomes[HITS].sum(axis=1)
            np.testing.assert_array_equal(eligible, counts[f"{side}_eligible"])
            np.testing.assert_array_equal(trials, prior[f"{prefix}_trials_{situation}"])
            np.testing.assert_array_equal(hits, prior[f"{prefix}_success_{situation}"])
            hit_rates[side] = hits.div(trials.where(trials > 0))
            weighted_rates[side] = outcomes.dot(weights).div(eligible.where(eligible > 0))
            if situation == "risp":
                players[f"ruane_trials_{side}"] = trials
                players[f"ruane_bps_{side}"] = outcomes[HITS].dot([2, 3, 4, 5]).div(trials.where(trials > 0))
        for name, rates in (("rate", hit_rates), ("weighted", weighted_rates)):
            column = f"{name}_difference_{situation}"
            difference = rates["on"] - rates["off"]
            np.testing.assert_allclose(difference, players[column], rtol=0, atol=1e-12)
            players[column] = difference
    players["ruane_bps_difference"] = players.ruane_bps_on - players.ruane_bps_off
    return players


def paired_bootstrap(y, predictions, rng):
    """Compare fixed OOF predictions using the same sampled players for each model."""
    errors = np.column_stack([(y - predictions[model]) ** 2 for model in MODELS])
    columns = {model: i for i, model in enumerate(MODELS)}
    draws = []
    for start in range(0, REPLICATES, 256):
        ids = rng.integers(len(y), size=(min(256, REPLICATES - start), len(y)))
        mse = errors[ids].mean(axis=1)
        draws.append((mse, y[ids].var(axis=1)))
    mse = np.concatenate([batch[0] for batch in draws])
    variance = np.concatenate([batch[1] for batch in draws])
    if np.any(variance == 0):
        raise ValueError("Undefined bootstrap R²")
    observed = errors.mean(axis=0)
    for raw, lrt in COMPARISONS:
        a, b = columns[raw], columns[lrt]
        for metric, estimate, values in (
            ("cv_r2_gain", (observed[a] - observed[b]) / y.var(), (mse[:, a] - mse[:, b]) / variance),
            ("cv_rmse_reduction", np.sqrt(observed[a]) - np.sqrt(observed[b]),
             np.sqrt(mse[:, a]) - np.sqrt(mse[:, b])),
        ):
            low, high = np.quantile(values, [.025, .975])
            yield dict(raw=raw, lrt=lrt, metric=metric, estimate=estimate, ci_low=low, ci_high=high,
                       replicates=REPLICATES, seed=SEED)


def plot_performance(performance, path):
    primary = performance.query("min_pa == 2000")
    colors = [{"A": "#718096", "B": "#31768b", "W": "#a8522c"}[m[0]] for m in primary.model]
    fig, axes = plt.subplots(1, 2, figsize=(9, 4.8), sharey=True, layout="constrained")
    for ax, metric, label in zip(axes, ["cv_r2", "cv_rmse"], ["CV R² (higher is better)", "CV RMSE (lower is better)"]):
        bars = ax.barh(primary.model, primary[metric], color=colors)
        ax.bar_label(bars, fmt="%.3f", padding=3)
        ax.set(xlabel=label, xlim=(0, primary[metric].max() * 1.22))
        ax.grid(axis="x", alpha=.18)
        ax.set_axisbelow(True)
    axes[0].invert_yaxis()
    fig.suptitle("Out-of-fold Clutch predictions | PA ≥ 2,000")
    fig.savefig(path, dpi=175)
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=ROOT / "Results/Appendix_A")
    args = parser.parse_args()

    players, samples = load_samples()
    players = player_metrics(players.set_index("batter"))
    prior_dir = WEIGHTED / "External_Benchmark"
    prior_predictions = pd.read_csv(prior_dir / "predictions.csv")
    prior_performance = pd.read_csv(prior_dir / "performance.csv").set_index(["min_pa", "model"])
    performance, coefficients, predictions, bootstrap = [], [], [], []
    rng = np.random.default_rng(SEED)
    for cutoff, (sample, folds, _) in samples.items():
        sample = players.loc[sample.batter]
        y = sample[TARGET].to_numpy()
        oof = {}
        for model, features in MODELS.items():
            x = sample[features].to_numpy()
            if not np.isfinite(x).all():
                raise ValueError(f"Missing predictors at {cutoff} PA for {model}")
            fit = fit_ols(x, y)
            oof[model], _ = cross_validate(x, y, folds)
            fitted_metrics = metrics(y, fit.fitted)
            df = len(y) - len(features) - 1
            summary = dict(adjusted_r2=1 - (1 - fitted_metrics["r2"]) * (len(y) - 1) / df,
                           **fitted_metrics,
                           **{f"cv_{key}": val for key, val in metrics(y, oof[model]).items()})
            if model in PRIOR_MODELS:
                saved = prior_predictions.query("min_pa == @cutoff and model == @model")
                np.testing.assert_array_equal(sample.index, saved.batter)
                np.testing.assert_array_equal(folds + 1, saved.fold)
                np.testing.assert_array_equal(y, saved.observed)
                np.testing.assert_allclose(fit.fitted, saved.fitted, rtol=0, atol=1e-10)
                np.testing.assert_allclose(oof[model], saved.out_of_fold, rtol=0, atol=1e-10)
                np.testing.assert_allclose(list(summary.values()), prior_performance.loc[
                    (cutoff, model), list(summary)].to_numpy(dtype=float), rtol=0, atol=1e-10)
            performance.append(dict(min_pa=cutoff, model=model, n=len(y), predictors=len(features), **summary))
            for term, estimate, se in zip(["intercept", *features], fit.beta, fit.se):
                coefficients.append(dict(min_pa=cutoff, model=model, term=term, estimate=estimate, hc3_se=se))
            predictions.append(pd.DataFrame(dict(min_pa=cutoff, model=model, batter=sample.index,
                total_pa=sample.total_pa.to_numpy(), fold=folds + 1, observed=y, fitted=fit.fitted,
                out_of_fold=oof[model])))
        bootstrap.extend(dict(min_pa=cutoff, **row) for row in paired_bootstrap(y, oof, rng))

    out = args.output_dir
    (out / "figures").mkdir(parents=True, exist_ok=True)
    performance = pd.DataFrame(performance)
    tables = dict(players=players.reset_index(), performance=performance, coefficients=pd.DataFrame(coefficients),
                  predictions=pd.concat(predictions, ignore_index=True),
                  bootstrap_comparisons=pd.DataFrame(bootstrap))
    for name, frame in tables.items():
        frame.to_csv(out / f"{name}.csv", index=False)
    plot_performance(performance, out / "figures/cv_performance.png")
    print(performance.round(5).to_string(index=False))
    print(tables["bootstrap_comparisons"].round(5).to_string(index=False))


if __name__ == "__main__":
    main()
