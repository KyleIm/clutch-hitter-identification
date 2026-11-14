"""Compare Retrosheet situational scores with the Baseball-Reference benchmark."""
import argparse
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats
import matplotlib.pyplot as plt

from analyze_risp_lips import row_correlation

ROOT = Path(__file__).resolve().parents[1]
CUTOFFS = {1000: 1343, 2000: 861, 3000: 595}
OURS = ["score_risp", "score_lips", "rate_difference_risp", "rate_difference_lips"]
EXTERNAL = ["period_clutch_estimate", "period_wpa"]
METRICS = OURS + EXTERNAL
LABELS = ["RISP S", "LIPS S", "RISP hit-rate difference", "LIPS hit-rate difference",
          "Clutch estimate", "WPA"]


def williams(r_lips, r_risp, r_between, n):
    """One-sided Williams test for two Pearson correlations sharing a variable."""
    determinant = 1 - r_lips**2 - r_risp**2 - r_between**2 + 2*r_lips*r_risp*r_between
    average = (r_lips + r_risp) / 2
    denominator = 2*(n-1)/(n-3)*determinant + average**2*(1-r_between)**3
    statistic = (r_lips-r_risp)*np.sqrt((n-1)*(1+r_between)/denominator)
    return statistic, stats.t.sf(statistic, n-3)


def bootstrap(values, draws, rng):
    """Resample complete player rows and rerank within each Spearman draw."""
    blocks = []
    for start in range(0, draws, 128):
        ids = rng.integers(len(values), size=(min(128, draws-start), len(values)))
        rows = values[ids].transpose(2, 0, 1)
        estimates = []
        for matrix in (rows, stats.rankdata(rows, axis=-1)):
            estimates.append(np.stack([
                row_correlation(matrix[i], matrix[j])
                for i in range(4) for j in (4, 5)
            ], axis=1))
        blocks.append(np.stack(estimates, axis=1))
    return np.concatenate(blocks)


def partial_pearson(x, y, control):
    design = np.column_stack((np.ones(len(control)), control))
    values = np.column_stack((x, y))
    residuals = values - design @ np.linalg.lstsq(design, values, rcond=None)[0]
    return stats.pearsonr(*residuals.T).statistic


def load_data():
    step1 = pd.read_csv(ROOT / "Results/RISP_LIPS/players.csv",
                        usecols=["batter", "player_name", "total_pa", *OURS])
    bench = pd.read_csv(ROOT / "Data/BaseballReference/bbref_1998_2025_wpa_matched.csv",
                        usecols=["batter", "bbref_id", "total_pa", "bbref_pa", *EXTERNAL])
    if step1.batter.isna().any() or bench.batter.isna().any() or (
        bench.bbref_id.isna().any() or not bench.bbref_id.is_unique
    ):
        raise ValueError("Missing or duplicate identifiers")
    data = step1.merge(bench, on="batter", suffixes=("", "_benchmark"),
                       how="outer", validate="one_to_one", indicator=True)
    if len(data) != 5716 or not data._merge.eq("both").all() or not (
        data.total_pa.eq(data.total_pa_benchmark).all()
    ):
        raise ValueError("Expected 5,716 matched hitters with identical Retrosheet PA")
    return data.drop(columns=["_merge", "total_pa_benchmark"]).sort_values("batter")


def plots(samples, correlation, matrices, directory):
    for index, target in enumerate(EXTERNAL):
        fig, axes = plt.subplots(2, 3, figsize=(11, 6), sharex="row", sharey=True,
                                layout="constrained")
        for col, (cutoff, sample) in enumerate(samples.items()):
            for row, metric in enumerate(OURS[:2]):
                ax = axes[row, col]
                ax.scatter(sample[metric], sample[target], s=10, alpha=.45, color="#19647e")
                ax.set(title=f"{cutoff:,}+ PA | n={len(sample):,}", xlabel=LABELS[row],
                       ylabel=LABELS[4+index] if col == 0 else "")
                ax.axvline(0, color=".7", lw=.7)
                ax.axhline(0, color=".7", lw=.7)
        fig.savefig(directory / f"{target}_scatter.png", dpi=170)
        plt.close(fig)

    fig, axes = plt.subplots(2, 3, figsize=(11, 5.5), layout="constrained")
    for col, (cutoff, sample) in enumerate(samples.items()):
        for row, target in enumerate(EXTERNAL):
            ax = axes[row, col]
            ax.hist(sample[target], bins=30, color="#19647e")
            ax.set(title=f"{cutoff:,}+ PA", xlabel=LABELS[row+4], ylabel="Players")
    fig.savefig(directory / "benchmark_distributions.png", dpi=170)
    plt.close(fig)

    fig, axes = plt.subplots(1, 3, figsize=(13, 4), layout="constrained")
    short = ["RISP S", "LIPS S", "RISP diff.", "LIPS diff.", "Clutch", "WPA"]
    for ax, (cutoff, matrix) in zip(axes, matrices.items()):
        img = ax.imshow(matrix, cmap="RdBu_r", vmin=-1, vmax=1)
        ax.set(title=f"{cutoff:,}+ PA", xticks=range(6), yticks=range(6),
               xticklabels=short, yticklabels=short)
        ax.tick_params(axis="x", labelrotation=45)
        for i in range(6):
            for j in range(6):
                value = matrix.iloc[i, j]
                ax.text(j, i, f"{value:.2f}", ha="center", va="center",
                        color="white" if abs(value) > .65 else "black", fontsize=8)
    fig.colorbar(img, ax=axes, shrink=.75, label="Pearson r")
    fig.savefig(directory / "correlation_matrix.png", dpi=170)
    plt.close(fig)

    fig, axes = plt.subplots(2, 2, figsize=(9, 6), sharex=True, sharey=True,
                            layout="constrained")
    for row, method in enumerate(("pearson", "spearman")):
        for col, target in enumerate(EXTERNAL):
            ax = axes[row,col]
            for i, metric in enumerate(OURS):
                d = correlation[(correlation.method == method) &
                                (correlation.external == target) &
                                (correlation.metric == metric)]
                offset = (i-1.5)*45
                ax.errorbar(d.min_pa+offset, d.coefficient,
                            yerr=[d.coefficient-d.ci_low, d.ci_high-d.coefficient],
                            marker="o", capsize=3, label=LABELS[i])
            ax.axhline(0,color=".7",lw=.7)
            ax.set(title=f"{method.title()} | {LABELS[col+4]}", xticks=list(CUTOFFS),
                   xlabel="Minimum career PA" if row == 1 else "")
    axes[0,0].legend(fontsize=7)
    fig.savefig(directory / "correlation_comparison.png", dpi=170)
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=ROOT / "Results/External_Benchmark")
    parser.add_argument("--bootstrap", type=int, default=10000)
    parser.add_argument("--seed", type=int, default=20261114)
    args = parser.parse_args()
    if args.bootstrap < 10000:
        parser.error("Use at least 10,000 bootstrap resamples")
    data = load_data()
    rng = np.random.default_rng(args.seed)
    summaries, correlations, tests, draws, sensitivity, coverage, matrix_rows, examples = (
        [], [], [], [], [], [], [], []
    )
    samples, matrices = {}, {}
    for cutoff in (0, *CUTOFFS):
        eligible = data[data.total_pa >= cutoff]
        finite = np.isfinite(eligible[METRICS])
        sample = eligible[finite.all(axis=1)]
        coverage.append({"min_pa": cutoff, "matched_ids": len(eligible), "complete": len(sample),
                         "pa_discrepancies": eligible.bbref_pa.ne(eligible.total_pa).sum(),
                         **{f"missing_{m}": (~finite[m]).sum() for m in METRICS}})
        if cutoff == 0:
            continue
        if len(eligible) != CUTOFFS[cutoff] or len(sample) != len(eligible):
            raise ValueError(f"Unexpected sample size or missing data at {cutoff} PA")
        samples[cutoff] = sample
        n = len(sample)
        values = sample[METRICS].to_numpy()
        for target in EXTERNAL:
            series = sample[target]
            q1, median, q3 = series.quantile([.25,.5,.75])
            iqr = q3-q1
            summaries.append(dict(min_pa=cutoff, metric=target, n=n, mean=series.mean(),
                                  sd=series.std(), minimum=series.min(), q1=q1, median=median,
                                  q3=q3, maximum=series.max(), skewness=series.skew(),
                                  iqr_outliers=((series<q1-1.5*iqr)|(series>q3+1.5*iqr)).sum()))
        pearson_matrix = sample[METRICS].corr()
        matrices[cutoff] = pearson_matrix
        for method in ("pearson", "spearman"):
            matrix = sample[METRICS].corr(method=method)
            for m, row in matrix.iterrows():
                matrix_rows.append(dict(min_pa=cutoff, method=method, metric=m, **row.to_dict()))
        boot = bootstrap(values, args.bootstrap, rng)
        if not np.isfinite(boot).all():
            raise ValueError("Undefined bootstrap correlation")
        for method_idx, method in enumerate(("pearson","spearman")):
            fn = stats.pearsonr if method_idx == 0 else stats.spearmanr
            for k, (metric, target) in enumerate((m,t) for m in OURS for t in EXTERNAL):
                estimate = fn(sample[metric],sample[target])
                if method_idx == 0:
                    lo,hi = estimate.confidence_interval()
                else:
                    lo,hi = np.quantile(boot[:,method_idx,k],[.025,.975])
                correlations.append(dict(min_pa=cutoff,method=method,metric=metric,external=target,
                                         n=n,coefficient=estimate.statistic,p_two_sided=estimate.pvalue,
                                         ci_low=lo,ci_high=hi))
            r_risp = fn(values[:,0],values[:,4]).statistic
            r_lips = fn(values[:,1],values[:,4]).statistic
            r_between = fn(values[:,0],values[:,1]).statistic
            delta_boot = boot[:,method_idx,2]-boot[:,method_idx,0]
            lo,hi = np.quantile(delta_boot,[.025,.975])
            t,p = williams(r_lips,r_risp,r_between,n) if method_idx == 0 else (np.nan,np.nan)
            tests.append(dict(min_pa=cutoff,method=method,n=n,r_risp=r_risp,r_lips=r_lips,
                              r_between=r_between,delta=r_lips-r_risp,ci_low=lo,ci_high=hi,
                              williams_t=t,df=n-3 if method_idx == 0 else np.nan,p_one_sided=p,
                              resamples=args.bootstrap,seed=args.seed))
            draws.extend(dict(min_pa=cutoff,method=method,resample=i,delta=d)
                         for i,d in enumerate(delta_boot,1))
        pa = sample.total_pa.to_numpy()
        for metric in METRICS:
            for method, fn in (("pearson",stats.pearsonr),("spearman",stats.spearmanr)):
                result = fn(pa,sample[metric])
                sensitivity.append(dict(min_pa=cutoff,analysis="association_with_pa",method=method,
                                        metric=metric,external="total_pa",n=n,
                                        coefficient=result.statistic,p_two_sided=result.pvalue))
        for metric in OURS:
            for target in EXTERNAL:
                x,y = sample[metric],sample[target]
                sensitivity.append(dict(min_pa=cutoff,analysis="control_log_pa",method="pearson",
                                        metric=metric,external=target,n=n,
                                        coefficient=partial_pearson(x,y,np.log(pa))))
                for method, fn in (("pearson",stats.pearsonr),("spearman",stats.spearmanr)):
                    result = fn(x,y*600/pa)
                    sensitivity.append(dict(min_pa=cutoff,analysis="external_per_600_pa",method=method,
                                            metric=metric,external=target,n=n,
                                            coefficient=result.statistic,p_two_sided=result.pvalue))
        for metric in OURS[:2]:
            ranks = sample[[metric, EXTERNAL[0]]].rank(pct=True)
            midpoint_product = (ranks[metric]-.5)*(ranks[EXTERNAL[0]]-.5)
            for kind, ascending in (("agreement",False),("disagreement",True)):
                for idx in midpoint_product.sort_values(ascending=ascending,kind="stable").index[:3]:
                    row = sample.loc[idx]
                    examples.append(dict(min_pa=cutoff,metric=metric,kind=kind,batter=row.batter,
                                         player_name=row.player_name,score=row[metric],
                                         clutch=row[EXTERNAL[0]],score_percentile=ranks.loc[idx,metric],
                                         clutch_percentile=ranks.loc[idx,EXTERNAL[0]]))
    out = args.output_dir
    (out/"figures").mkdir(parents=True,exist_ok=True)
    correlation = pd.DataFrame(correlations)
    tables = dict(players=data, descriptives=pd.DataFrame(summaries), correlations=correlation,
                  dependent_tests=pd.DataFrame(tests), bootstrap_deltas=pd.DataFrame(draws),
                  pa_sensitivity=pd.DataFrame(sensitivity), sample_coverage=pd.DataFrame(coverage),
                  correlation_matrices=pd.DataFrame(matrix_rows), examples=pd.DataFrame(examples))
    for name, table in tables.items():
        table.to_csv(out/f"{name}.csv",index=False)
    plots(samples,correlation,matrices,out/"figures")
    print(tables["dependent_tests"].to_string(index=False))


if __name__ == "__main__":
    main()
