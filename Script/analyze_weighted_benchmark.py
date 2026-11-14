"""Compare binomial and weighted Clutch models on the original validation folds."""
import argparse
from itertools import combinations
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

from analyze_clutch_regression import BASE, CUTOFFS, ROOT, SEED, cross_validate, fit_ols, metrics, plt
from analyze_external_benchmark import partial_pearson
from analyze_risp_lips import row_correlation

WEIGHTED = ROOT / "Results/Weighted_ON_OFF"
SCORES = ["RISP", "LIPS", "wRISP", "wLIPS"]
TARGET = "period_clutch_estimate"
BENCHMARKS = [TARGET, "period_wpa"]
MODELS = {"B1": ["RISP"], "B2": ["LIPS"], "B3": ["RISP", "LIPS"],
          "W1": ["wRISP"], "W2": ["wLIPS"], "W3": ["wRISP", "wLIPS"]}
RAW = ["rate_difference_risp", "rate_difference_lips", "weighted_difference_risp",
       "weighted_difference_lips"]


def load_samples():
    data = pd.read_csv(BASE / "players.csv").rename(columns={"score_risp": "RISP", "score_lips": "LIPS"})
    if len(data) != 5716 or data.batter.isna().any():
        raise ValueError("Expected all 5,716 Retrosheet IDs")
    for situation, original, weighted in zip(("risp", "lips"), SCORES[:2], SCORES[2:]):
        baseline = pd.read_csv(WEIGHTED / "Baseline" / f"{situation}_players.csv")
        data = data.merge(baseline[["batter", "total_pa", "binomial_score", "weighted_score", "weighted_difference"]],
                          on="batter", how="outer", validate="one_to_one", suffixes=("", "_check"),
                          indicator=True)
        if not data._merge.eq("both").all():
            raise ValueError("Player IDs differ")
        np.testing.assert_array_equal(data.total_pa, data.total_pa_check)
        np.testing.assert_array_equal(data[original], data.binomial_score)
        data = data.drop(columns=["total_pa_check", "binomial_score", "_merge"]).rename(
            columns={"weighted_score": weighted, "weighted_difference": f"weighted_difference_{situation}"})
    if data.bbref_id.isna().any() or not data.bbref_id.is_unique:
        raise ValueError("Expected unique Baseball-Reference IDs")
    reference = pd.read_csv(BASE / "Regression/predictions.csv")
    rng = np.random.default_rng(SEED)
    samples = {}
    for cutoff, n in CUTOFFS.items():
        sample = data[data.total_pa.ge(cutoff)].sort_values("batter").reset_index(drop=True)
        if len(sample) != n or not np.isfinite(sample[SCORES + BENCHMARKS + RAW]).all().all():
            raise ValueError(f"Incomplete sample at {cutoff} PA")
        old = reference[reference.min_pa.eq(cutoff)]
        folds = np.empty(n, dtype=int)
        for fold, ids in enumerate(np.array_split(rng.permutation(n), 5)):
            folds[ids] = fold
        for model in ("RISP", "LIPS", "Combined"):
            saved = old[old.model.eq(model)]
            np.testing.assert_array_equal(sample.batter, saved.batter)
            np.testing.assert_array_equal(sample.total_pa, saved.total_pa)
            np.testing.assert_array_equal(folds + 1, saved.fold)
            np.testing.assert_array_equal(sample[TARGET], saved.observed)
        samples[cutoff] = (sample, folds, old)
    return data.sort_values("batter"), samples


def bootstrap(sample, predictions, rng, draws):
    source = sample[[*SCORES, TARGET]].to_numpy()
    y, b, w = predictions.T
    rows = []
    for start in range(0, draws, 256):
        ids = rng.integers(len(y), size=(min(256, draws-start), len(y)))
        sampled = source[ids].transpose(2, 0, 1)
        result = {}
        for method, values in (("pearson", sampled), ("spearman", stats.rankdata(sampled, axis=-1))):
            for i, situation in enumerate(("RISP", "LIPS")):
                result[f"{method}_{situation}_clutch_gain"] = (
                    row_correlation(values[i+2], values[4]) - row_correlation(values[i], values[4]))
        result["cv_pearson_gain"] = row_correlation(y[ids], w[ids]) - row_correlation(y[ids], b[ids])
        b_error, w_error = (y-b)[ids], (y-w)[ids]
        b_mse, w_mse = (b_error**2).mean(1), (w_error**2).mean(1)
        result["cv_r2_gain"] = (b_mse-w_mse)/y[ids].var(1)
        result["cv_rmse_reduction"] = np.sqrt(b_mse)-np.sqrt(w_mse)
        result["cv_mae_reduction"] = abs(b_error).mean(1)-abs(w_error).mean(1)
        rows.append(pd.DataFrame(result))
    return pd.concat(rows, ignore_index=True)


def run_models(sample, folds, old, cutoff, tables):
    y = sample[TARGET].to_numpy()
    fitted_results, oof_results, slope_tests = {}, {}, {}
    for model, features in MODELS.items():
        x = sample[features].to_numpy()
        fit = fit_ols(x, y)
        oof, fold_results = cross_validate(x, y, folds)
        if model.startswith("B"):
            saved = old[old.model.eq({"B1": "RISP", "B2": "LIPS", "B3": "Combined"}[model])]
            np.testing.assert_allclose(fit.fitted, saved.fitted, rtol=0, atol=1e-10)
            np.testing.assert_allclose(oof, saved.out_of_fold, rtol=0, atol=1e-10)
        n, k = len(y), len(fit.beta)
        df = n-k
        critical = stats.t.ppf(.975, df)
        t = fit.beta / fit.se
        p = 2*stats.t.sf(abs(t), df)
        for i, term in enumerate(["intercept", *features]):
            beta, se = fit.beta[i], fit.se[i]
            tables["coefficients"].append(dict(min_pa=cutoff, model=model, term=term, estimate=beta,
                hc3_se=se, ci_low=beta-critical*se, ci_high=beta+critical*se, p=p[i], df=df,
                standardized=beta*x[:,i-1].std()/y.std() if i else np.nan))
        summary, cv = metrics(y, fit.fitted), metrics(y, oof)
        fitted_results[model] = summary
        oof_results[model] = cv
        slope_tests[model] = (t, p, df)
        tables["performance"].append(dict(min_pa=cutoff, model=model, n=n,
            adjusted_r2=1-(1-summary["r2"])*(n-1)/df, **summary,
            **{f"cv_{key}": value for key, value in cv.items()}))
        tables["cv_folds"].extend(dict(min_pa=cutoff, model=model, **row) for row in fold_results)
        tables["predictions"].append(pd.DataFrame(dict(min_pa=cutoff, model=model, batter=sample.batter,
            fold=folds+1, observed=y, fitted=fit.fitted, out_of_fold=oof)))
        if model.endswith("3"):
            mse = np.sum(fit.residual**2)/df
            student = fit.residual/np.sqrt(mse*(1-fit.leverage))
            cooks = student**2 * fit.leverage/(k*(1-fit.leverage))
            tables["diagnostics"].append(pd.DataFrame(dict(min_pa=cutoff, model=model,
                batter=sample.batter, fitted=fit.fitted, residual=fit.residual,
                studentized_residual=student, leverage=fit.leverage, cooks_distance=cooks)))
    for family in ("B", "W"):
        full = family+"3"
        t, p, df = slope_tests[full]
        for reduced, added in ((family+"1", 2), (family+"2", 1)):
            tables["nested_comparisons"].append(dict(min_pa=cutoff, full=full, reduced=reduced,
                added=MODELS[full][added-1], delta_r2=fitted_results[full]["r2"]-fitted_results[reduced]["r2"],
                hc3_wald_f=t[added]**2, df_num=1, df_den=df, p=p[added]))
    return oof_results


def figures(primary, results, out):
    fig, axes = plt.subplots(2, 2, figsize=(10, 8), layout="constrained")
    for row, method in enumerate(("pearson", "spearman")):
        for col, scores in enumerate((SCORES[:2], SCORES[2:])):
            names = [*scores, *BENCHMARKS]
            corr = primary[names].corr(method=method)
            ax = axes[row,col]
            img = ax.imshow(corr, cmap="RdBu_r", vmin=-1, vmax=1)
            labels = [*scores, "Clutch", "WPA"]
            ax.set(title=f"{method.title()} | {'Binomial' if col == 0 else 'Weighted'}",
                   xticks=range(4), yticks=range(4), xticklabels=labels, yticklabels=labels)
            for i in range(4):
                for j in range(4):
                    v = corr.iloc[i,j]
                    ax.text(j,i,f"{v:.2f}",ha="center",va="center",color="white" if abs(v)>.65 else "black")
    fig.colorbar(img, ax=axes, shrink=.8)
    fig.savefig(out/"correlation_matrices.png",dpi=175)
    plt.close(fig)

    fig, axes = plt.subplots(2,2,figsize=(9,7),sharex=True,sharey=True,layout="constrained")
    for ax, score in zip(axes.flat, SCORES):
        ax.scatter(primary[score],primary[TARGET],s=9,alpha=.4)
        ax.set(xlabel=score,ylabel="Clutch estimate")
    fig.savefig(out/"scores_vs_clutch.png",dpi=175)
    plt.close(fig)

    fig, axes = plt.subplots(2,2,figsize=(9,7),sharex=True,sharey=True,layout="constrained")
    for row,column in enumerate(("fitted","out_of_fold")):
        for col,model in enumerate(("B3","W3")):
            d=results["predictions"].query("min_pa == 2000 and model == @model")
            ax=axes[row,col]
            ax.scatter(d[column],d.observed,s=9,alpha=.4)
            lim=[d.observed.min(),d.observed.max()]
            ax.plot(lim,lim,color=".6")
            ax.set(title=model,xlabel=column.replace("_"," ").capitalize()+" Clutch",ylabel="Observed Clutch")
    fig.savefig(out/"combined_predictions.png",dpi=175)
    plt.close(fig)

    fig, axes = plt.subplots(2,3,figsize=(12,7),sharex="col",sharey="col",layout="constrained")
    for row,model in enumerate(("B3","W3")):
        d=results["diagnostics"].query("min_pa == 2000 and model == @model")
        axes[row,0].scatter(d.fitted,d.residual,s=9,alpha=.4)
        axes[row,0].axhline(0,color=".6")
        axes[row,0].set(title=model,xlabel="Fitted Clutch",ylabel="Residual")
        stats.probplot(d.studentized_residual,plot=axes[row,1])
        axes[row,2].scatter(d.leverage,d.cooks_distance,s=9,alpha=.4)
        axes[row,2].set(xlabel="Leverage",ylabel="Cook's distance")
    fig.savefig(out/"residual_diagnostics.png",dpi=175)
    plt.close(fig)

    fig, axes = plt.subplots(2,2,figsize=(10,7),layout="constrained")
    performance=results["performance"]
    for row,metric in enumerate(("cv_r2","cv_rmse")):
        d=performance.query("min_pa == 2000")
        axes[row,0].bar(d.model,d[metric],color=["#31768b"]*3+["#a8522c"]*3)
        axes[row,0].set(title="2,000+ PA",ylabel=metric.replace("cv_","CV ").upper())
        for model in MODELS:
            d=performance[performance.model.eq(model)]
            axes[row,1].plot(d.min_pa,d[metric],marker="o",label=model)
        axes[row,1].set(xticks=list(CUTOFFS),xlabel="Minimum PA")
    axes[0,1].legend(ncol=2)
    fig.savefig(out/"cv_performance.png",dpi=175)
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bootstrap", type=int, default=10000)
    parser.add_argument("--output-dir", type=Path, default=WEIGHTED / "External_Benchmark")
    args = parser.parse_args()
    if args.bootstrap < 10000:
        parser.error("At least 10,000 resamples required")
    data, samples = load_samples()
    keys = ("coefficients", "performance", "cv_folds", "predictions", "diagnostics",
            "nested_comparisons", "correlations", "pa_sensitivity", "bootstrap_comparisons", "coverage")
    tables = {key: [] for key in keys}
    rng = np.random.default_rng(SEED)
    for cutoff,(sample,folds,old) in samples.items():
        tables["coverage"].append(dict(min_pa=cutoff,n=len(sample),missing_inputs=0,
                                       prior_membership_and_folds_verified=True))
        oof = run_models(sample,folds,old,cutoff,tables)
        n = len(sample)
        for x,y in [*combinations(SCORES+BENCHMARKS,2), *((x,TARGET) for x in RAW)]:
            for method,fn in (("pearson",stats.pearsonr),("spearman",stats.spearmanr)):
                fit=fn(sample[x],sample[y])
                tables["correlations"].append(dict(min_pa=cutoff,x=x,y=y,method=method,
                    n=n,coefficient=fit.statistic,p_two_sided=fit.pvalue))
        pa=sample.total_pa
        for x in SCORES+RAW+BENCHMARKS:
            for method,fn in (("pearson",stats.pearsonr),("spearman",stats.spearmanr)):
                tables["pa_sensitivity"].append(dict(min_pa=cutoff,x=x,y="total_pa",method=method,
                    analysis="association_with_pa",coefficient=fn(sample[x],pa).statistic))
        for x in SCORES+RAW:
            for y in BENCHMARKS:
                tables["pa_sensitivity"].append(dict(min_pa=cutoff,x=x,y=y,method="pearson",
                    analysis="control_log_pa",coefficient=partial_pearson(sample[x],sample[y],np.log(pa))))
                for method,fn in (("pearson",stats.pearsonr),("spearman",stats.spearmanr)):
                    tables["pa_sensitivity"].append(dict(min_pa=cutoff,x=x,y=y,method=method,
                        analysis="external_per_600_pa",coefficient=fn(sample[x],sample[y]*600/pa).statistic))
        predictions=pd.concat(tables["predictions"][-6:])
        draws=bootstrap(sample,np.column_stack((sample[TARGET],
            *[predictions.loc[predictions.model.eq(model),"out_of_fold"] for model in ("B3","W3")])),
            rng,args.bootstrap)
        if not np.isfinite(draws).all().all():
            raise ValueError("Undefined bootstrap metric")
        observed={}
        for method,fn in (("pearson",stats.pearsonr),("spearman",stats.spearmanr)):
            for original,weighted in zip(SCORES[:2],SCORES[2:]):
                observed[f"{method}_{original}_clutch_gain"]=(
                    fn(sample[weighted],sample[TARGET]).statistic-fn(sample[original],sample[TARGET]).statistic)
        for key,direction in (("pearson",1),("r2",1),("rmse",-1),("mae",-1)):
            label=f"cv_{key}_{'gain' if direction==1 else 'reduction'}"
            observed[label]=direction*(oof["W3"][key]-oof["B3"][key])
        for key,estimate in observed.items():
            lo,hi=draws[key].quantile([.025,.975])
            base_key=key.split("_")[1]
            tables["bootstrap_comparisons"].append(dict(min_pa=cutoff,metric=key,estimate=estimate,
                ci_low=lo,ci_high=hi,relative=estimate/oof["B3"][base_key] if key.startswith("cv_") else np.nan,
                replicates=args.bootstrap,seed=SEED))
    results={key:pd.concat(value,ignore_index=True) if isinstance(value[0],pd.DataFrame) else pd.DataFrame(value)
             for key,value in tables.items()}
    results["players"]=data
    matrices=[]
    for cutoff,(sample,_,_) in samples.items():
        for method in ("pearson","spearman"):
            matrix=sample[SCORES+BENCHMARKS].corr(method=method)
            matrices.append(matrix.rename_axis("variable").reset_index().assign(min_pa=cutoff,method=method))
    results["correlation_matrices"]=pd.concat(matrices,ignore_index=True)
    out=args.output_dir
    (out/"figures").mkdir(parents=True,exist_ok=True)
    for name,frame in results.items():
        frame.to_csv(out/f"{name}.csv",index=False)
    figures(samples[2000][0],results,out/"figures")
    print(results["performance"].round(5).to_string(index=False))
    print(results["bootstrap_comparisons"].round(5).to_string(index=False))


if __name__ == "__main__":
    main()
