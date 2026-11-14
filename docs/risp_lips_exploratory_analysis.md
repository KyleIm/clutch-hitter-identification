# RISP–LIPS exploratory analysis

Run from the repository root with the dependencies in `requirements.txt`.

```bash
python Script/analyze_risp_lips.py --simulations 10000 --seed 20251113
python -m unittest discover -s tests
```

Use `--output-dir` to write a run elsewhere. The analysis reads the 28
tracked compact season files and the tracked RISP and LIPS marginal counts.
See the [likelihood derivation](binomial_on_off_likelihood_derivation.md)
for the signed score. The existing labeling functions use runner state
before the final pitch for RISP and runner state at the start of the
plate appearance for the bases-loaded LIPS exception.

## Coverage and outcomes

The script joins the marginal summaries one-to-one on Retrosheet batter ID
and checks total PA equality and date coverage. It assigns each PA to one of
four disjoint categories using two Boolean flags: neither, RISP only, LIPS
only, or both. It sums plate appearances, eligible trials, and hits within
each category, then reconstructs both marginal summaries and checks the
observed PA, hits, trials, failures, exclusions, rates, and signed scores.
It independently verifies the squared scores against a 2×2 G statistic.

A trial is a hit or a classified failure. Walks (including intentional
walks), hit-by-pitches, catcher interference and sacrifice bunts are excluded.
Sacrifice flies count as failures, so the hit-rate denominator differs from
official at-bats. The analysis uses paired complete cases. Players without
an eligible trial in one of the ON/OFF groups have an undefined score.

## Descriptive analysis and conventional inference

The primary sample uses 2,000 total PA. The 1,000 and 3,000 cutoffs are
nested sensitivity samples. All-player and cutoff-specific exclusions are
listed in `sample_coverage.csv`. Scores quantify evidence for a within-player
difference. Raw hit-rate differences quantify the magnitude. Rates in CSVs
are fractions, and the scatterplot expresses differences in percentage points.

Pearson 95% intervals use Fisher's transformation. Spearman 95% intervals
use the 2.5th and 97.5th percentiles of 2,000 paired player bootstrap
resamples. Conventional two-sided p-values against zero come from SciPy's
[pearsonr](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.pearsonr.html)
and [spearmanr](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.spearmanr.html).
These intervals and p-values describe the paired-player relationship under
their usual sampling assumptions. The zero null can differ from the
overlap-aware null.

Each tail contains ceil(0.05 × n) players with ties broken by ascending
Retrosheet ID. The extremes table lists five players per tail and metric, and
the five largest signed score gaps in each direction. Score gaps are descriptive
and can reflect different marginal trial counts and league baselines.

## Overlap-aware null

For each player, estimate a pooled hit probability from all eligible trials.
In each draw, hold the four trial counts fixed and draw independent category
hit counts with that same player probability. Reconstruct both sets of ON/OFF
counts from the single draw, using the same simulated achievements in the
shared categories. Compute Pearson and Spearman correlations of the two
signed score vectors within each PA cutoff. The same simulated populations
are used across the nested samples.

The reported central 95% interval describes the distribution of simulated
correlations. The excess is observed correlation minus mean simulated
correlation. The prespecified one-sided p-value is
`(1 + count(simulated >= observed)) / (1 + simulations)`.
Results across cutoffs and correlation methods are related and should not be
treated as independent replications. The null assumes a constant hit
probability per player. League-wide situation effects, relief-pitcher
quality, and other contextual effects can influence the observed results.
The test does not estimate repeatability or identify intrinsic clutch skill.
