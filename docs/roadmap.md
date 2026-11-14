# Roadmap

- [Step 1 — RISP–LIPS correlation](analysis/01_risp_lips_correlation.md) is complete.
- [Step 2 — Baseball-Reference external benchmark](analysis/02_external_benchmark.md) is complete.

## Step 3: Weighted ON/OFF Framework

[Step 3.1](analysis/03_weighted_on_off.md) established the fixed weights and
outcome counts. [Step 3.2](analysis/03_2_weighted_validation.md) derived and
validated the signed multinomial likelihood ratio. Later steps will
analyze the weighted baseline and evaluate it against Baseball-Reference
Clutch.

### Deferred Joint RISP–LIPS Index

The joint model remains deferred while the weighted marginal framework is developed.

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

## Optional Extensions

- Calibrate individual marginal scores under player-level null models and compare positive and negative tail frequencies at `|S| > 2` and `|S| > 3`.
- Account for multiple testing across players, for example with false discovery rate control or population-level simulations.
- Examine league-adjusted situational baselines and how the pooled hit-rate gaps affect the score distributions.
- Compare empirically standardized scores while preserving the distinction between relative scores and detection significance.
- Assess leave-one-season-out sensitivity and study year-to-year repeatability as a separate question.
- Estimate upper limits for player-specific effects after checking marginal calibration and league baselines.
