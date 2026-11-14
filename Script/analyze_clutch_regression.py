"""Fit and cross-validate three OLS approximations of historical Clutch."""
import argparse
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

from analyze_risp_lips import plt

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "Results/External_Benchmark"
TARGET = "period_clutch_estimate"
SCORES = ["score_risp", "score_lips"]
MODELS = {"RISP": [0], "LIPS": [1], "Combined": [0, 1]}
CUTOFFS = {1000: 1343, 2000: 861, 3000: 595}
SEED = 20261114


@dataclass
class Fit:
    beta: np.ndarray
    se: np.ndarray
    fitted: np.ndarray
    residual: np.ndarray
    leverage: np.ndarray


def design(x):
    return np.column_stack((np.ones(len(x)), x))


def fit_ols(x, y):
    matrix = design(x)
    q, r = np.linalg.qr(matrix)
    beta = np.linalg.solve(r, q.T @ y)
    fitted = matrix @ beta
    residual = y - fitted
    leverage = (q * q).sum(axis=1)
    influence = np.linalg.solve(r, q.T) * (residual / (1 - leverage))
    se = np.sqrt((influence * influence).sum(axis=1))
    return Fit(beta, se, fitted, residual, leverage)


def analytical_r2(x, y):
    r_risp, r_lips = np.corrcoef(np.column_stack((x, y)), rowvar=False)[:2, 2]
    r_between = np.corrcoef(x, rowvar=False)[0, 1]
    r2 = (r_risp**2 + r_lips**2 - 2*r_risp*r_lips*r_between) / (1-r_between**2)
    return r_risp, r_lips, r_between, r2


def metrics(y, prediction):
    errors = y - prediction
    sse = errors @ errors
    centered = y - y.mean()
    return dict(pearson=stats.pearsonr(y, prediction).statistic,
                spearman=stats.spearmanr(y, prediction).statistic,
                r2=1-sse/(centered @ centered), rmse=np.sqrt(np.mean(errors**2)),
                mae=np.mean(np.abs(errors)))


def cross_validate(x, y, folds):
    matrix = design(x)
    prediction = np.full(len(y), np.nan)
    scores = []
    for fold in range(5):
        held = folds == fold
        beta = np.linalg.lstsq(matrix[~held], y[~held], rcond=None)[0]
        prediction[held] = matrix[held] @ beta
        scores.append(dict(fold=fold+1, train_n=(~held).sum(), test_n=held.sum(),
                           **metrics(y[held], prediction[held])))
    if not np.isfinite(prediction).all():
        raise ValueError("Missing out-of-fold predictions")
    return prediction, scores


def draw_figures(pred, performance, diagnostics, out):
    for column, label in (("fitted", "Fitted"), ("out_of_fold", "Out-of-fold predicted")):
        fig, axes = plt.subplots(3, 3, figsize=(10, 9), sharex=True, sharey=True, layout="constrained")
        lo, hi = pred.observed.min(), pred.observed.max()
        for row, cutoff in enumerate(CUTOFFS):
            for col, model in enumerate(MODELS):
                points = pred[(pred.min_pa == cutoff) & (pred.model == model)]
                ax = axes[row, col]
                ax.scatter(points[column], points.observed, s=8, alpha=.38, color="#19647e")
                ax.plot([lo, hi], [lo, hi], color=".6", lw=1)
                ax.set(title=f"{model} | {cutoff:,}+ PA",
                       xlabel=f"{label} Clutch" if row == 2 else "",
                       ylabel="Observed Clutch" if col == 0 else "")
        fig.savefig(out / f"{column}_scatter.png", dpi=170)
        plt.close(fig)

    fig, axes = plt.subplots(2, 2, figsize=(9, 6), sharex=True, layout="constrained")
    for row, metric in enumerate(("pearson", "r2")):
        for col, kind in enumerate(("in_sample", "pooled_oof")):
            ax = axes[row, col]
            for model in MODELS:
                group = performance[(performance.model == model) & (performance.evaluation == kind)]
                ax.plot(group.min_pa, group[metric], marker="o", label=model)
            ax.set(title=kind.replace("_", " ").title(), xticks=list(CUTOFFS),
                   ylabel="Pearson r" if row == 0 else "R-squared",
                   xlabel="Minimum career PA" if row == 1 else "")
    axes[0, 0].legend()
    fig.savefig(out / "performance_comparison.png", dpi=170)
    plt.close(fig)

    fig, axes = plt.subplots(3, 3, figsize=(11, 9), layout="constrained")
    for row, cutoff in enumerate(CUTOFFS):
        d = diagnostics[diagnostics.min_pa == cutoff]
        ax = axes[row, 0]
        ax.scatter(d.fitted, d.residual, s=8, alpha=.4)
        ax.axhline(0, color=".55")
        bins = d.groupby(pd.qcut(d.fitted, 10, duplicates="drop"), observed=True)
        means = bins[["fitted", "residual"]].mean()
        ax.plot(means.fitted, means.residual, color="#b24c36", marker="o", ms=3)
        ax.set(xlabel="Fitted Clutch", ylabel="Residual", title=f"{cutoff:,}+ PA")
        stats.probplot(d.studentized_residual, plot=axes[row, 1])
        axes[row, 2].scatter(d.leverage, d.cooks_distance, s=8, alpha=.4)
        axes[row, 2].axhline(4/len(d), color="#b24c36", lw=1)
        axes[row, 2].set(xlabel="Leverage", ylabel="Cook's distance")
    fig.savefig(out / "combined_diagnostics.png", dpi=170)
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=BASE / "Regression")
    args = parser.parse_args()
    data = pd.read_csv(BASE / "players.csv", usecols=["batter", "player_name", "total_pa", *SCORES, TARGET])
    if len(data) != 5716 or data.batter.isna().any() or not data.batter.is_unique:
        raise ValueError("Expected 5,716 unique nonempty batter IDs")
    data = data.sort_values("batter")
    rng = np.random.default_rng(SEED)
    coefficients, performance, nested, identity, folds, predictions, diagnostics, checks = (
        [], [], [], [], [], [], [], []
    )
    for cutoff, expected in CUTOFFS.items():
        sample = data[data.total_pa >= cutoff].reset_index(drop=True)
        if len(sample) != expected or not np.isfinite(sample[SCORES + [TARGET]]).all().all():
            raise ValueError(f"Unexpected size or missing data for {cutoff} PA")
        x, y = sample[SCORES].to_numpy(), sample[TARGET].to_numpy()
        n = len(y)
        fold_ids = np.empty(n, dtype=int)
        for fold, indices in enumerate(np.array_split(rng.permutation(n), 5)):
            fold_ids[indices] = fold
        comparison = {}
        for model, columns in MODELS.items():
            predictors = x[:, columns]
            fit = fit_ols(predictors, y)
            k = len(fit.beta)
            df = n - k
            critical = stats.t.ppf(.975, df)
            coefficient_t = fit.beta / fit.se
            coefficient_p = 2 * stats.t.sf(abs(coefficient_t), df)
            standardized = fit.beta[1:] * predictors.std(axis=0) / y.std()
            for i, term in enumerate(["intercept", *[SCORES[c] for c in columns]]):
                coefficients.append(dict(min_pa=cutoff, model=model, term=term,
                    coefficient=fit.beta[i], hc3_se=fit.se[i], t=coefficient_t[i], df=df,
                    p=coefficient_p[i], ci_low=fit.beta[i]-critical*fit.se[i],
                    ci_high=fit.beta[i]+critical*fit.se[i],
                    standardized=np.nan if i == 0 else standardized[i-1]))
            fitted = metrics(y, fit.fitted)
            performance.append(dict(min_pa=cutoff, model=model, evaluation="in_sample", n=n,
                                    adjusted_r2=1-(1-fitted["r2"])*(n-1)/df, **fitted))
            oof, scores = cross_validate(predictors, y, fold_ids)
            pooled = metrics(y, oof)
            performance.append(dict(min_pa=cutoff, model=model, evaluation="pooled_oof", n=n, **pooled))
            comparison[model] = (fitted, pooled)
            for score in scores:
                folds.append(dict(min_pa=cutoff, model=model, **score))
            fold_frame = pd.DataFrame(scores)[list(pooled)]
            for label, summary in (("fold_mean", fold_frame.mean()), ("fold_sd", fold_frame.std(ddof=1))):
                performance.append(dict(min_pa=cutoff, model=model, evaluation=label, **summary))
            predictions.append(sample[["batter", "player_name", "total_pa"]].assign(
                min_pa=cutoff, model=model, fold=fold_ids+1, observed=y, fitted=fit.fitted, out_of_fold=oof))
            if model != "Combined":
                continue
            r_risp, r_lips, r_between, r2 = analytical_r2(x, y)
            np.testing.assert_allclose(fitted["r2"], r2, rtol=0, atol=1e-12)
            identity.append(dict(min_pa=cutoff, r_risp_clutch=r_risp, r_lips_clutch=r_lips,
                                 r_risp_lips=r_between, analytical_r2=r2, fitted_r2=fitted["r2"],
                                 absolute_error=abs(fitted["r2"]-r2)))
            for term_index, reduced in ((1, "LIPS"), (2, "RISP")):
                base_fit, base_oof = comparison[reduced]
                result = dict(min_pa=cutoff, reduced=reduced, added=["RISP", "LIPS"][term_index-1],
                              hc3_wald_f=coefficient_t[term_index]**2,
                              df_num=1, df_den=df, p=coefficient_p[term_index])
                for prefix, combined, single in (("in_sample", fitted, base_fit),
                                                   ("oof", pooled, base_oof)):
                    for metric in ("pearson", "r2"):
                        gain = combined[metric] - single[metric]
                        result[f"{prefix}_{metric}_gain"] = gain
                        result[f"{prefix}_{metric}_relative_gain"] = gain / single[metric]
                nested.append(result)
            mse = (fit.residual @ fit.residual)/df
            studentized = fit.residual/np.sqrt(mse*(1-fit.leverage))
            cooks = studentized**2 * fit.leverage/(k*(1-fit.leverage))
            diagnostics.append(sample[["batter", "player_name"]].assign(
                min_pa=cutoff, fitted=fit.fitted, residual=fit.residual, leverage=fit.leverage,
                studentized_residual=studentized, cooks_distance=cooks))
            aux = design(x)
            square = fit.residual**2
            aux_fitted = aux @ np.linalg.lstsq(aux, square, rcond=None)[0]
            lm = n*(1-np.var(square-aux_fitted)/np.var(square))
            residual_means = pd.Series(fit.residual).groupby(
                pd.qcut(fit.fitted, 10, duplicates="drop"), observed=True).mean()
            checks.append(dict(min_pa=cutoff, koenker_lm=lm, koenker_p=stats.chi2.sf(lm, 2),
                               cooks_over_4_n=(cooks > 4/n).sum(), max_cooks=cooks.max(),
                               most_influential_batter=sample.batter.iloc[np.argmax(cooks)],
                               min_residual_decile_mean=residual_means.min(),
                               max_residual_decile_mean=residual_means.max()))

    out = args.output_dir
    (out / "figures").mkdir(parents=True, exist_ok=True)
    tables = dict(coefficients=pd.DataFrame(coefficients), performance=pd.DataFrame(performance),
                  nested_comparisons=pd.DataFrame(nested), analytical_verification=pd.DataFrame(identity),
                  cv_folds=pd.DataFrame(folds), predictions=pd.concat(predictions, ignore_index=True),
                  diagnostics=pd.concat(diagnostics, ignore_index=True), diagnostic_summary=pd.DataFrame(checks))
    for name, table in tables.items():
        table.to_csv(out / f"{name}.csv", index=False)
    draw_figures(tables["predictions"], tables["performance"], tables["diagnostics"], out / "figures")
    print(tables["performance"].query("evaluation in ['pooled_oof', 'in_sample']").to_string(index=False))


if __name__ == "__main__":
    main()
