"""Validate the weighted ON/OFF statistic without ranking players."""
import argparse
from pathlib import Path
import numpy as np
import pandas as pd
from scipy import stats
from analyze_risp_lips import plt
from lima_histogram_RISP_sample import binomial_on_off_s
from multinomial_on_off import fit_weighted_on_off

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "Results/Weighted_ON_OFF"
SEED = 20261114
BINOMIAL_TOL = 2e-7


def verify_reduction():
    rows = []
    for situation in ("risp", "lips"):
        frame = pd.read_csv(DATA / f"{situation}_player_counts.csv")
        outcomes = ["zero", "single", "double", "triple", "home_run"]
        on, off = [frame[[f"{side}_{c}" for c in outcomes]].to_numpy()
                   for side in ("on", "off")]
        expected = binomial_on_off_s(on[:, 1:].sum(1), on[:, 0],
                                     off[:, 1:].sum(1), off[:, 0])
        actual = np.array([fit_weighted_on_off(a, b, [0, 1, 1, 1, 1]).score
                           for a, b in zip(on, off)])
        np.testing.assert_allclose(actual, expected, atol=BINOMIAL_TOL, rtol=0)
        rows.append(dict(situation=situation, players=len(frame),
                         defined=np.isfinite(expected).sum(),
                         undefined=np.isnan(expected).sum(),
                         max_abs_error=np.nanmax(abs(actual-expected)),
                         absolute_tolerance=BINOMIAL_TOL))
    return pd.DataFrame(rows)


def configurations(p, w):
    same_mean = p.copy()
    # Replace some singles with a mixture of outs and HR of equal mean.
    moved = p[3] / 2
    same_mean[3] -= moved
    same_mean[0] += moved * (1 - w[3]/w[-1])
    same_mean[-1] += moved * w[3]/w[-1]
    sparse = np.array([.985, .004, .001, .008, .001, .0001, .0009])
    for name, n, m, on, off in (
        ("null_balanced", 300, 300, p, p),
        ("null_risp", 500, 1500, p, p),
        ("null_lips", 250, 1750, p, p),
        ("null_equal_mean_risp", 500, 1500, same_mean, p),
        ("null_equal_mean_lips", 250, 1750, same_mean, p),
        ("null_sparse", 15, 135, sparse, sparse),
    ):
        yield name, n, m, on, off, True
    for n, m in ((100, 300), (500, 1500)):
        for shift in (.02, .05):
            on = p.copy()
            on[0] -= shift
            on[-1] += shift
            yield f"alt_{n}_{shift:.2f}", n, m, on, p, False


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--simulations", type=int, default=10000)
    parser.add_argument("--output-dir", type=Path, default=DATA / "Validation")
    args = parser.parse_args()
    if args.simulations < 1:
        parser.error("simulation count must be positive")
    out = args.output_dir
    out.mkdir(parents=True, exist_ok=True)
    verify_reduction().to_csv(out / "binomial_reduction.csv", index=False)
    weights = pd.read_csv(DATA / "fixed_weights.csv")
    names, w = weights.outcome.tolist(), weights.weight.to_numpy()
    frame = pd.read_csv(DATA / "risp_player_counts.csv")
    pooled = np.array([frame[f"on_{c}"].sum()+frame[f"off_{c}"].sum() for c in names])
    probabilities = pooled / pooled.sum()
    rng = np.random.default_rng(SEED)
    summaries, failures, inputs, null_scores = [], [], [], {}
    for name, n, m, p, q, is_null in configurations(probabilities, w):
        for group, probs in (("on", p), ("off", q)):
            inputs.append(dict(configuration=name, group=group, **dict(zip(names, probs))))
        on = rng.multinomial(n, p, size=args.simulations)
        off = rng.multinomial(m, q, size=args.simulations)
        fitted = []
        for index, (a, b) in enumerate(zip(on, off)):
            try:
                fitted.append(fit_weighted_on_off(a, b, w))
            except RuntimeError as exc:
                failures.append(dict(configuration=name, draw=index+1, reason=str(exc)))
        if not fitted:
            raise RuntimeError(f"No successful fits for {name}: {failures[-1]}")
        scores = np.array([fit.score for fit in fitted])
        ts = scores**2
        if is_null:
            null_scores[name] = scores
        q025, median, q975 = np.quantile(scores, [.025, .5, .975])
        summaries.append(dict(configuration=name, is_null=is_null, on_trials=n, off_trials=m,
                              seed=SEED, population_gap=(p-q)@w, success=len(scores),
                              failed=args.simulations-len(scores), mean=scores.mean(),
                              sd=scores.std(ddof=1), median=median, q025=q025, q975=q975,
                              rejection_05=(ts>stats.chi2.ppf(.95,1)).mean(),
                              rejection_01=(ts>stats.chi2.ppf(.99,1)).mean(),
                              positive_score=(scores>0).mean(), zero_score=(scores==0).mean(),
                              ts_q95=np.quantile(ts,.95), ts_q99=np.quantile(ts,.99),
                              max_null_mean_gap=max(fit.mean_gap for fit in fitted),
                              max_iterations=max(fit.iterations for fit in fitted)))
        print(name, summaries[-1], flush=True)
    pd.DataFrame(summaries).to_csv(out / "simulation_summary.csv", index=False)
    pd.DataFrame(inputs).to_csv(out / "simulation_probabilities.csv", index=False)
    pd.DataFrame(failures, columns=["configuration","draw","reason"]).to_csv(
        out / "optimizer_failures.csv", index=False)
    figure_dir = out / "figures"
    figure_dir.mkdir(exist_ok=True)
    for kind in ("histogram", "qq"):
        fig, axes = plt.subplots(2, 3, figsize=(11, 7), layout="constrained")
        for ax, (name, scores) in zip(axes.flat, null_scores.items()):
            if kind == "histogram":
                x = np.linspace(-4,4,300)
                ax.hist(scores, bins=45, density=True, color="#31768b")
                ax.plot(x, stats.norm.pdf(x), color="#aa552b")
                ax.set(xlabel="Signed weighted statistic", ylabel="Density")
            else:
                theoretical, observed = stats.probplot(scores, fit=False)
                ax.scatter(theoretical, observed, s=2, color="#31768b")
                ax.plot(theoretical, theoretical, color="#aa552b")
                ax.set(xlabel="Normal quantile", ylabel="Observed quantile")
            ax.set_title(name.removeprefix("null_").replace("_", " ").title())
        fig.savefig(figure_dir / f"null_{kind}.png", dpi=170)
        plt.close(fig)


if __name__ == "__main__":
    main()
