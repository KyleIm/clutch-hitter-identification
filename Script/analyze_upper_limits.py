"""Reproduce Step 2 player limits, population summaries, and figures."""
import argparse
from dataclasses import asdict
from pathlib import Path
from time import perf_counter

import numpy as np
import pandas as pd
from scipy.integrate import quad
from scipy.stats import spearmanr

from analyze_risp_lips import ROOT, plt
from binomial_upper_limit import binomial_upper_limit, difference_density, posterior_parameters

CUTOFFS = (1000, 2000, 3000)
THRESHOLDS = (3, 1.645)
SITUATIONS = ("RISP", "LIPS")
COLORS = {"RISP": "#236b87", "LIPS": "#b4532d"}


def validate():
    rng = np.random.default_rng(20261114)
    cases = {
        "sparse": (0, 1, 1, 1), "symmetric": (4, 10, 4, 10),
        "equal_large": (40, 100, 40, 100), "positive": (7, 10, 3, 10),
        "negative": (3, 10, 7, 10), "all_hits": (5, 5, 5, 5),
        "zero_hits": (0, 5, 0, 5), "imbalanced": (1, 4, 250, 1000),
    }
    rows = []
    for case, counts in cases.items():
        start = perf_counter()
        result = binomial_upper_limit(*counts)
        elapsed = perf_counter() - start
        on, off = posterior_parameters(*counts)

        def density(d):
            return difference_density(d, on, off)

        negative = quad(density, -1, 0, epsabs=1e-9)[0]
        positive = quad(density, 0, 1, epsabs=1e-9)[0]
        mass = quad(density, 0, result.upper_limit, epsabs=1e-9)[0] / positive
        draws = rng.beta(*on, size=300000) - rng.beta(*off, size=300000)
        selected = draws[draws >= 0]
        mc_positive = len(selected) / len(draws)
        mc_mass = np.mean(selected <= result.upper_limit)
        np.testing.assert_allclose([negative + positive, positive, mass],
                                   [1, result.positive_probability, .95], rtol=0, atol=2e-8)
        for observed, expected, n in ((mc_positive, positive, len(draws)), (mc_mass, .95, len(selected))):
            assert abs(observed - expected) < 6 * np.sqrt(expected * (1 - expected) / n)
        rows.append(dict(case=case, posterior_mass=negative + positive, direct_positive=positive,
                         direct_conditional_mass=mass, mc_positive=mc_positive,
                         mc_conditional_mass=mc_mass, mc_positive_draws=len(selected),
                         solve_seconds=elapsed, **asdict(result)))
    start = perf_counter()
    extreme = binomial_upper_limit(0, 1000, 1000, 1000)
    # For Beta(1,n+1) and Beta(n+1,1), Q(d)/Q(0) = (1-d)^(2n+2).
    exact = -np.expm1(np.log(.05) / 2002)
    np.testing.assert_allclose(extreme.upper_limit, exact, rtol=0, atol=1e-12)
    rows.append(dict(case="underflow", analytic_limit=exact, solve_seconds=perf_counter() - start,
                     **asdict(extreme)))
    assert rows[2]["upper_limit"] < rows[1]["upper_limit"]
    return pd.DataFrame(rows)


def player_results(source):
    rows = []
    for situation in SITUATIONS:
        suffix = situation.lower()
        fields = [f"{name}_{suffix}" for name in
                  ("n_success", "n_trials", "b_success", "b_trials", "score")]
        for batter, name, pa, h1, n1, h0, n0, score in source[
            ["batter", "player_name", "total_pa", *fields]
        ].itertuples(index=False, name=None):
            row = dict(situation=situation, batter=batter, player_name=name, total_pa=pa,
                       on_hits=h1, on_trials=n1, off_hits=h0, off_trials=n0, score=score,
                       on_rate=h1/n1 if n1 else np.nan, off_rate=h0/n0 if n0 else np.nan)
            if not n1 or not n0:
                rows.append(dict(row, status="zero_trials"))
                continue
            if not np.isfinite(score):
                raise ValueError(f"Missing signed score for {batter} {situation}")
            try:
                result = binomial_upper_limit(h1, n1, h0, n0)
            except ArithmeticError as exc:
                raise ArithmeticError(f"{batter} {situation}: {exc}") from exc
            rows.append(dict(row, status="valid", **asdict(result),
                             difference_pp=100 * result.observed_difference,
                             upper_limit_pp=100 * result.upper_limit))
    players = pd.DataFrame(rows)
    for threshold, column in zip(THRESHOLDS, ("detection_3", "detection_1_645")):
        players[column] = np.select(
            [players.status.ne("valid"), players.score.ge(threshold), players.score.le(-threshold)],
            ["zero_trials", "positive", "negative"], default="neither")
    return players


def summarize(players):
    rows = []
    for situation in SITUATIONS:
        for cutoff in CUTOFFS:
            sample = players.query("situation == @situation and total_pa >= @cutoff and status == 'valid'")
            for threshold in THRESHOLDS:
                nondetections = sample[sample.score.lt(threshold)]
                for group, frame in (("all", sample), ("nondetection", nondetections)):
                    val = frame.upper_limit_pp
                    rows.append(dict(situation=situation, min_pa=cutoff, threshold=threshold,
                                     group=group, n=len(frame), valid=len(sample),
                                     positive=int(sample.score.ge(threshold).sum()),
                                     negative=int(sample.score.le(-threshold).sum()),
                                     neither=int(sample.score.abs().lt(threshold).sum()),
                                     nondetections=len(nondetections),
                                     mean_pp=val.mean(), median_pp=val.median(), sd_pp=val.std(),
                                     p05_pp=val.quantile(.05), p25_pp=val.quantile(.25),
                                     p75_pp=val.quantile(.75), p95_pp=val.quantile(.95),
                                     spearman_on_trials=spearmanr(val, frame.on_trials).statistic,
                                     spearman_total_trials=spearmanr(val, frame.on_trials + frame.off_trials).statistic,
                                     spearman_signed_score=spearmanr(val, frame.score).statistic))
    return pd.DataFrame(rows)


def examples(primary):
    frames = []
    for situation in SITUATIONS:
        sample = primary.query("situation == @situation")
        near = sample[sample.score.abs().le(.25)]
        negative = sample[sample.score.le(-3)]
        for label, frame in (("near_zero_weak", near.nlargest(1, "upper_limit")),
                             ("near_zero_strong", near.nsmallest(1, "upper_limit")),
                             ("negative_tight", negative.nsmallest(1, "upper_limit"))):
            frames.append(frame.assign(example=label))
    return pd.concat(frames, ignore_index=True)


def figures(players, primary, illustrative, out):
    plt.rcParams.update({"axes.spines.top": False, "axes.spines.right": False, "font.size": 10})

    def save(fig, name):
        fig.savefig(out / f"{name}.png", dpi=225)
        plt.close(fig)

    fig, axes = plt.subplots(2, 3, figsize=(11, 6), layout="constrained")
    for ax, row in zip(axes.flat, illustrative.itertuples(index=False)):
        on, off = posterior_parameters(row.on_hits, row.on_trials, row.off_hits, row.off_trials)
        mean = on[0]/sum(on) - off[0]/sum(off)
        sd = np.sqrt(sum(a*b/((a+b)**2*(a+b+1)) for a, b in (on, off)))
        x = np.unique(np.r_[np.linspace(max(-1, min(0, mean-4*sd)),
                                        min(1, max(row.upper_limit, mean+4*sd)), 140),
                            0, row.upper_limit])
        y = np.array([difference_density(d, on, off) for d in x])
        ax.plot(100*x, y/100, color=COLORS[row.situation])
        ax.fill_between(100*x, y/100, where=(x >= 0) & (x <= row.upper_limit),
                        color=COLORS[row.situation], alpha=.25)
        ax.axvline(100*row.upper_limit, color=".25", linestyle="--",
                   label=f"95% UL {row.upper_limit_pp:.2f} pp")
        ax.set(title=f"{row.situation} | {row.player_name}", xlabel="ON − OFF (pp)", ylabel="Density per pp")
        ax.legend(frameon=False, fontsize=8)
    save(fig, "posterior_examples")

    fig, ax = plt.subplots(figsize=(7, 4), layout="constrained")
    for situation in SITUATIONS:
        for detected, linestyle, label in ((False, "-", "S < 3"), (True, "--", "S ≥ 3")):
            sample = primary[primary.situation.eq(situation) & primary.score.ge(3).eq(detected)]
            if not sample.empty:
                val = np.r_[0, np.sort(sample.upper_limit_pp)]
                ax.step(val, np.arange(len(val))/(len(val)-1), where="post",
                        color=COLORS[situation], linestyle=linestyle, label=f"{situation}, {label}")
    ax.set(xlabel="Conditional 95% upper limit (pp)", ylabel="Cumulative player fraction",
           title="Upper-limit distributions | PA ≥ 2,000")
    ax.legend(frameon=False)
    save(fig, "upper_limit_distributions")

    for column, label, name in (("on_trials", "ON eligible trials", "upper_limit_vs_trials"),
                                 ("score", "Signed binomial score", "upper_limit_vs_score")):
        fig, axes = plt.subplots(1, 2, figsize=(9, 4), sharey=True, layout="constrained")
        for ax, situation in zip(axes, SITUATIONS):
            sample = primary.query("situation == @situation")
            for status, marker, color in (("neither", "o", COLORS[situation]),
                                          ("negative", "v", "#5f478b"), ("positive", "^", "#237c52")):
                group = sample[sample.detection_3.eq(status)]
                ax.scatter(group[column], group.upper_limit_pp, s=13, alpha=.6, marker=marker,
                           color=color, label=status)
            ax.set(title=situation, xlabel=label)
            if column == "on_trials":
                ax.set_xscale("log")
        axes[0].set_ylabel("Conditional 95% upper limit (pp)")
        axes[1].legend(frameon=False)
        fig.suptitle("PA ≥ 2,000")
        save(fig, name)

    fig, axes = plt.subplots(1, 2, figsize=(8, 4), sharey=True, layout="constrained")
    for ax, situation in zip(axes, SITUATIONS):
        sample = players.query("situation == @situation and status == 'valid' and score < 3")
        ax.boxplot([sample.loc[sample.total_pa.ge(pa), "upper_limit_pp"] for pa in CUTOFFS])
        ax.set(title=situation, xlabel="Minimum total PA", xticks=[1, 2, 3], xticklabels=CUTOFFS)
    axes[0].set_ylabel("Conditional 95% upper limit (pp)")
    fig.suptitle("Positive nondetections (S < 3)")
    save(fig, "upper_limits_by_cutoff")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=ROOT / "Results/Upper_Limits")
    out = parser.parse_args().output_dir
    validation = validate()
    source = pd.read_csv(ROOT / "Results/RISP_LIPS/players.csv")
    if not source.batter.is_unique:
        raise ValueError("Expected unique player IDs")
    start = perf_counter()
    players = player_results(source)
    print(f"Player calculations: {perf_counter() - start:.2f} seconds")
    summary = summarize(players)
    primary = players.query("total_pa >= 2000 and status == 'valid'")
    illustrative = examples(primary)
    (out / "figures").mkdir(parents=True, exist_ok=True)
    for name, frame in (("players", players), ("population_summary", summary),
                        ("validation", validation), ("representative_players", illustrative)):
        frame.to_csv(out / f"{name}.csv", index=False)
    figures(players, primary, illustrative, out / "figures")
    print(players.groupby(["situation", "status"]).size().to_string())
    print(summary.query("group == 'nondetection'").round(4).to_string(index=False))


if __name__ == "__main__":
    main()
