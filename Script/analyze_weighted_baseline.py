"""Score and compare the weighted and binomial Retrosheet baselines."""
import argparse
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import norm

from analyze_risp_lips import ROOT, plt
from multinomial_on_off import ROOT_TOL, fit_weighted_on_off

DATA = ROOT / "Results/Weighted_ON_OFF"
CUTOFFS = {1000: 1343, 2000: 861, 3000: 595}


def score_players(counts, prior, situation, weights, solver=fit_weighted_on_off):
    for frame in (counts, prior):
        if frame.batter.isna().any() or not frame.batter.is_unique:
            raise ValueError("Missing or duplicate batter IDs")
    counts = counts.set_index("batter").sort_index()
    prior = prior.set_index("batter").sort_index()
    pd.testing.assert_index_equal(counts.index, prior.index)
    np.testing.assert_array_equal(counts.total_pa, prior.total_pa)
    columns = [[f"{side}_{name}" for name in weights.index] for side in ("on", "off")]
    on, off = [counts[cols].to_numpy() for cols in columns]
    w = weights.to_numpy()
    for side, matrix, prefix in (("on", on, "n"), ("off", off, "b")):
        eligible = matrix.sum(axis=1)
        np.testing.assert_array_equal(eligible, counts[f"{side}_eligible"])
        np.testing.assert_array_equal(eligible + counts[f"{side}_excluded"], prior[f"{prefix}_{situation}"])
        mean = np.divide(matrix @ w, eligible, out=np.full(len(counts), np.nan), where=eligible > 0)
        np.testing.assert_allclose(mean, counts[f"{side}_weighted_mean"], atol=1e-12, rtol=0)
    np.testing.assert_allclose(counts.weighted_difference,
                               counts.on_weighted_mean - counts.off_weighted_mean, atol=1e-12)
    diagnostics = []
    for batter, a, b, gap in zip(counts.index, on, off, counts.weighted_difference):
        row = dict(batter=batter, status="ok", weighted_score=np.nan, weighted_ts=np.nan,
                   iterations=np.nan, null_mean_gap_normalized=np.nan, error="")
        if min(a.sum(), b.sum()) == 0:
            row["status"] = "empty_group"
        else:
            try:
                fit = solver(a, b, w)
            except RuntimeError as exc:
                row.update(status="optimizer_failure", error=str(exc))
            else:
                expected_sign = 0 if abs(gap) <= ROOT_TOL * np.ptp(w) else np.sign(gap)
                if not np.isfinite(fit.score) or np.sign(fit.score) != expected_sign:
                    raise ValueError(f"Score sign mismatch or undefined fit for {situation}/{batter}")
                np.testing.assert_allclose(fit.score**2, fit.ts, atol=1e-10, rtol=1e-12)
                row.update(weighted_score=fit.score, weighted_ts=fit.ts, iterations=fit.iterations,
                           null_mean_gap_normalized=fit.mean_gap)
        diagnostics.append(row)
    counts["binomial_score"] = prior[f"score_{situation}"]
    return counts.join(pd.DataFrame(diagnostics).set_index("batter")).reset_index()


def pooled(frame, weights):
    hit_rate, production, trials = [], [], []
    for side in ("on", "off"):
        counts = frame[[f"{side}_{name}" for name in weights.index]].sum().set_axis(weights.index)
        hits = counts[["single", "double", "triple", "home_run"]].sum()
        original_trials = hits + counts["zero"]
        hit_rate.append(hits / original_trials)
        production.append(counts.dot(weights) / counts.sum())
        trials.append((original_trials, counts.sum()))
    for metric, values, index in (("hit_rate", hit_rate, 0), ("weighted_production", production, 1)):
        yield dict(metric=metric, on=values[0], off=values[1], difference=values[0]-values[1],
                   on_trials=trials[0][index], off_trials=trials[1][index])


def figures(players, out):
    primary = {s: frame[frame.total_pa.ge(2000)] for s, frame in players.items()}
    limit = max(np.ceil(frame[["binomial_score", "weighted_score"]].abs().max().max())
                for frame in primary.values())
    bins = np.linspace(-limit, limit, 37)
    x = np.linspace(-limit, limit, 400)
    for situation, sample in primary.items():
        for comparison in (False, True):
            fig, ax = plt.subplots(figsize=(8, 4.5), layout="constrained")
            if comparison:
                ax.hist(sample.binomial_score, bins=bins, density=True, histtype="step",
                        color="#aa552b", linewidth=2, label=situation.upper())
            ax.hist(sample.weighted_score, bins=bins, density=True, alpha=.44,
                    color="#31768b", label=f"w{situation.upper()}")
            ax.plot(x, norm.pdf(x), "--", color=".25", label="Asymptotic null N(0, 1)")
            ax.set(xlim=(-limit, limit), ylim=(0, .60), xlabel="Signed likelihood-ratio score",
                   ylabel="Density", title=f"{situation.upper()} | PA ≥ 2,000")
            ax.legend(frameon=False)
            stem = f"{situation}_comparison" if comparison else f"w{situation}_histogram"
            fig.savefig(out / f"{stem}.png", dpi=175)
            plt.close(fig)
    fig, axes = plt.subplots(1, 3, figsize=(11, 4), sharey=True, layout="constrained")
    for ax, cutoff in zip(axes, CUTOFFS):
        values = [frame.loc[frame.total_pa.ge(cutoff), col]
                  for frame in players.values() for col in ("binomial_score", "weighted_score")]
        ax.boxplot(values)
        ax.set(xticks=range(1, 5), xticklabels=["RISP", "wRISP", "LIPS", "wLIPS"],
               title=f"PA ≥ {cutoff:,}")
        ax.axhline(0, color=".6", lw=.7)
    axes[0].set_ylabel("Signed likelihood-ratio score")
    fig.savefig(out / "cutoff_boxplots.png", dpi=175)
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=DATA / "Baseline")
    args = parser.parse_args()
    out = args.output_dir
    (out / "figures").mkdir(parents=True, exist_ok=True)
    weights = pd.read_csv(DATA / "fixed_weights.csv").set_index("outcome").weight
    prior = pd.read_csv(ROOT / "Results/RISP_LIPS/players.csv")
    players, league, stats, rankings, checks, changes = {}, [], [], [], [], []
    for situation in ("risp", "lips"):
        source = pd.read_csv(DATA / f"{situation}_player_counts.csv")
        frame = score_players(source, prior, situation, weights)
        if len(frame) != 5716:
            raise ValueError("Expected 5,716 hitters")
        players[situation] = frame
        frame.to_csv(out / f"{situation}_players.csv", index=False)
        league.extend(dict(situation=situation, **row) for row in pooled(frame, weights))
        for cutoff in (0, *CUTOFFS):
            sample = frame[frame.total_pa.ge(cutoff)]
            status = sample.status.value_counts()
            checks.append(dict(situation=situation, min_pa=cutoff, players=len(sample),
                               defined=status.get("ok", 0), empty_group=status.get("empty_group", 0),
                               optimizer_failure=status.get("optimizer_failure", 0),
                               max_null_mean_gap=sample.null_mean_gap_normalized.max()))
            if cutoff == 0:
                continue
            if len(sample) != CUTOFFS[cutoff] or not sample.status.eq("ok").all():
                raise ValueError(f"Unexpected sample or failed fit at {situation}/{cutoff}; see player CSV")
            for label, col in ((situation.upper(), "binomial_score"), (f"w{situation.upper()}", "weighted_score")):
                scores = sample[col].dropna()
                stats.append(dict(situation=situation, min_pa=cutoff, metric=label, n=len(scores),
                                  mean=scores.mean(), median=scores.median(), sd=scores.std(),
                                  minimum=scores.min(), maximum=scores.max(), q05=scores.quantile(.05),
                                  q95=scores.quantile(.95), skewness=scores.skew()))
            fields = ["batter", "player_name", "total_pa", "on_eligible", "off_eligible",
                      "binomial_score", "weighted_score", "weighted_difference"]
            for tail in ("top", "bottom"):
                selected = sample.sort_values(["weighted_score", "batter"],
                                              ascending=[tail == "bottom", True]).head(10)
                rankings.append(selected[fields].assign(situation=situation, min_pa=cutoff,
                                                       tail=tail, rank=range(1, 11)))
            if cutoff == 2000:
                delta = sample.weighted_score - sample.binomial_score
                for direction in ("increase", "decrease"):
                    selected = sample.assign(score_change=delta).sort_values(
                        ["score_change", "batter"], ascending=[direction == "decrease", True]).head(5).copy()
                    for name, weight in weights.items():
                        selected[f"{name}_production_difference"] = weight * (
                            selected[f"on_{name}"]/selected.on_eligible -
                            selected[f"off_{name}"]/selected.off_eligible)
                    changes.append(selected.assign(situation=situation, direction=direction))
    tables = dict(league_production=pd.DataFrame(league), score_summary=pd.DataFrame(stats),
                  rankings=pd.concat(rankings), score_changes=pd.concat(changes),
                  integrity=pd.DataFrame(checks))
    for name, frame in tables.items():
        frame.to_csv(out / f"{name}.csv", index=False)
    figures(players, out / "figures")
    print(tables["league_production"].to_string(index=False))
    print(tables["score_summary"].round(4).to_string(index=False))
    print(tables["integrity"].to_string(index=False))


if __name__ == "__main__":
    main()
