# Roadmap

The portfolio’s next steps are joint modeling and external benchmarking.
See the [README analysis index](../README.md#analysis) for completed work.

## Step 2: Joint RISP–LIPS Likelihood-Ratio Analysis

Use the four mutually exclusive categories verified in [Step 1](analysis/01_risp_lips_correlation.md).

| Category | RISP | LIPS |
|---|---|---|
| A | No | No |
| B | Yes | No |
| C | No | Yes |
| D | Yes | Yes |

Use the verified hits and eligible batting trials for each category. The number of hits in category `j` can then be modeled as `H_j ~ Binomial(N_j, p_j)`.

A binomial logistic model can represent conditional RISP and LIPS effects:

`logit(p_j) = beta_0 + beta_R I_RISP,j + beta_L I_LIPS,j`.

The coefficients represent conditional situational effects on batting success probability. The joint null hypothesis is

`H_0: beta_R = beta_L = 0`.

The likelihood-ratio statistic is

`TS_joint = 2 (log L_alternative - log L_null)`.

Under standard regularity conditions, the asymptotic null distribution is chi-square with two degrees of freedom. This is an established likelihood-ratio methodology applied to a joint baseball situational model, not a newly invented statistical test.

- Fit the joint binomial logistic model for each eligible player.
- Calculate the joint likelihood-ratio statistic and estimate the RISP/LIPS coefficients.
- Evaluate the finite-sample null distribution of the joint likelihood-ratio statistic. Step 1 simulations calibrated the marginal score correlation.
- Investigate whether an interaction term between RISP and LIPS is necessary.
- Compare the joint results with the existing marginal RISP and LIPS significance statistics.
- Examine league-wide situational effects and whether an adjusted null model is appropriate.
- Check player-level sample sizes and potential separation problems before assuming the four category probabilities can be estimated reliably.

### Directional Joint Clutch Index

The project also aims to investigate a directional clutch index derived from the joint likelihood framework. This requires separating two related but distinct objects:

1. The joint likelihood-ratio statistic, which measures evidence against the null hypothesis that both situational effects are zero.
2. A directional clutch index, which would be intended to distinguish positive from negative situational batting performance.

The ordinary two-degree-of-freedom joint likelihood-ratio statistic is nonnegative and does not provide a natural sign. Constructing a signed index therefore requires an additional, explicitly justified definition of the direction of the combined effect.

Potential approaches for future investigation include:

- A prespecified linear contrast of the fitted RISP and LIPS coefficients.
- A constrained common-effect model, provided its assumptions can be justified.
- A covariance-aware directional statistic derived from the joint model.

No final directional index has been selected or validated. Any proposed index must be evaluated for statistical interpretation, null-distribution calibration, sensitivity to sample size, stability under different PA cutoffs, dependence on league-wide situational baselines, and potential double-counting of overlapping RISP/LIPS observations. A new directional index should not be labeled as a Z-score or statistical significance unless its calibration supports that interpretation.

## Step 3: External Benchmark Comparison

This analysis should be compared with existing sabermetric clutch measurements, especially FanGraphs Clutch and Ruane's RISP/non-RISP comparison using the difference in BPS (`BA + SLG`). FanGraphs Clutch is defined as `Clutch_FG = WPA / pLI - WPA / LI`.

The goal is to compare independently developed joint likelihood-based clutch measures with established metrics. FanGraphs Clutch should not be used to train the coefficients of the proposed joint index in the primary methodology; it should remain an external comparison benchmark.

- Obtain FanGraphs Clutch measurements for a period matching the Retrosheet dataset (1998-2025), subject to data availability.
- Match FanGraphs player identifiers with Retrosheet player identifiers.
- Match players and analysis periods across the different metrics.
- Compare the existing marginal RISP/LIPS significance statistics with FanGraphs Clutch.
- Compare the proposed directional joint clutch index with FanGraphs Clutch after the index has been statistically defined and validated.
- Calculate Pearson and Spearman correlations between RISP significance, LIPS significance, the proposed joint measures, and established clutch metrics.
- Generate scatter plots and compare overlap among top-ranked, bottom-ranked, and extreme performers.
- Identify players whose likelihood-based rankings differ substantially from their FanGraphs Clutch ranking.
- Evaluate whether the joint index provides information distinct from existing win-probability-based metrics.
- Consider the influence of career length and batting opportunities on cross-metric comparisons.
- Discuss differences in the underlying estimands: statistical evidence for hit-rate changes versus situational run or win contributions.
- Do not treat the unsigned joint likelihood-ratio statistic as directly equivalent to signed FanGraphs Clutch. If the unsigned statistic is compared with the magnitude of FanGraphs Clutch, the limitations of that comparison should be stated explicitly.
- Avoid claiming that the proposed framework is superior solely because it produces a likelihood-ratio significance.

## Optional Extensions

- Calibrate individual marginal scores under player-level null models and compare positive and negative tail frequencies at `|S| > 2` and `|S| > 3`.
- Account for multiple testing across players, for example with false discovery rate control or population-level simulations.
- Examine league-adjusted situational baselines and how the pooled hit-rate gaps affect the score distributions.
- Compare empirically standardized scores while preserving the distinction between relative scores and detection significance.
- Assess leave-one-season-out sensitivity and study year-to-year repeatability as a separate question.
- Estimate upper limits for player-specific effects after checking marginal calibration and league baselines.
