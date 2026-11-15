# Step 2 — Bayesian upper limits for binomial ON/OFF

[Bayesian upper-limit derivation in Appendix C](appendix_c_mathematical_derivations.md#c4--bayesian-upper-limits-for-binomial-onoff).

The signed binomial ON/OFF score measures evidence for a difference in
situational hit rates. A positive nondetection leaves open a range of
plausible positive effects. The Zech-inspired Bayesian binomial upper
limit answers how large that difference could be, conditional on the
difference being positive. RISP and LIPS are evaluated separately on
the existing Retrosheet 1998–2025 binomial trials.
[Mathematical derivation and primary sources](../methodology/binomial_upper_limit.md)

## Samples and classification

Calculate a limit for every batter with eligible observations on both
sides, then apply total-PA cutoffs of 1,000, 2,000 (primary), and 3,000.
At threshold c, positive detection means S ≥ c, negative detection
means S ≤ −c, and neither means −c < S < c. The positive-nondetection
subset S < c includes negative detections. The primary threshold is 3
and the sensitivity threshold is 1.645. A percentage point (pp) equals
0.01 in hit-rate probability.

## Numerical validation

The analysis checks normalization and conditional mass by directly
integrating the difference density in eight representative cases, with
independent samples of 300,000 Beta pairs per case as a second check.
The direct normalization, positive probability, and conditional mass
must agree within 2 × 10⁻⁸. The sampling checks use six Monte Carlo
standard errors as a numerical diagnostic. At an observed rate of
0.4 on each side, increasing trials per side from 10 to 100 tightens
the limit. In the opposing 1,000-trial all-hit and zero-hit stress case,
the analytic conditional tail is (1 − d)^2002. Its limit is 0.1495 pp
and the natural log of the positive posterior mass remains finite
(about −1,384), even though its probability underflows in double
precision. Per-case timings are in the validation CSV.

## Results

Of 5,716 players, 4,882 had valid RISP comparisons and 4,092 had valid
LIPS comparisons. One or both sides had zero eligible trials for the
other 834 RISP and 1,624 LIPS rows. All 8,974 valid comparisons
converged on the final run. Player calculations took 133.95 seconds
on the run machine. The largest reported relative integration error
was below 10⁻⁸, and the maximum absolute discrepancy from conditional
mass 0.95 was 4.0 × 10⁻¹⁴.

| Situation | Minimum PA | Valid | Positive | Neither | Negative | S < 3 | Mean UL (pp) | Median UL (pp) | SD (pp) | 5th–95th percentile (pp) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| RISP | 1,000 | 1,343 | 2 | 1,337 | 4 | 1,341 | 4.30 | 3.91 | 2.02 | 1.83–8.32 |
| RISP | 2,000 | 861 | 2 | 857 | 2 | 859 | 3.43 | 3.17 | 1.36 | 1.68–5.91 |
| RISP | 3,000 | 595 | 0 | 593 | 2 | 595 | 3.02 | 2.86 | 1.11 | 1.56–5.11 |
| LIPS | 1,000 | 1,343 | 0 | 1,303 | 40 | 1,343 | 4.04 | 3.65 | 2.01 | 1.59–7.84 |
| LIPS | 2,000 | 861 | 0 | 831 | 30 | 861 | 3.19 | 2.91 | 1.34 | 1.47–5.76 |
| LIPS | 3,000 | 595 | 0 | 567 | 28 | 595 | 2.75 | 2.51 | 1.08 | 1.38–4.82 |

Upper-limit summaries in the table are for S < 3. At the alternative
threshold S < 1.645, the primary RISP subset has 831 players, including
73 negative detections, and a median limit of 3.10 pp. The corresponding
LIPS subset has 855 players, including 234 negative detections, and a
median limit of 2.89 pp. The population CSV includes summaries for all
valid players and nondetections under both thresholds.

### Representative players at PA ≥ 2,000

| Situation | Player | ON trials | OFF trials | S | Positive probability | 95% UL (pp) |
|---|---|---:|---:|---:|---:|---:|
| RISP | Brendan Donovan | 384 | 1,393 | 0.18 | 0.579 | 5.52 |
| RISP | Todd Helton | 2,067 | 5,890 | −0.24 | 0.408 | 2.16 |
| RISP | Casey Blake | 1,256 | 3,291 | −3.09 | 0.00103 | 1.18 |
| LIPS | Mike Jacobs | 288 | 1,674 | −0.05 | 0.492 | 5.55 |
| LIPS | Miguel Tejada | 1,259 | 7,147 | −0.17 | 0.438 | 2.59 |
| LIPS | Freddie Freeman | 1,242 | 6,938 | −3.49 | 0.000258 | 1.05 |

The first two players per situation minimize or maximize the limit
among primary-sample players with |S| ≤ 0.25 (listed widest first).
The third has the tightest limit among players with S ≤ −3.

## Interpretation

The signed score assesses evidence for a difference, while the upper
limit constrains its magnitude under the positive-effect condition.
Among primary nondetections, the limit's Spearman correlation with
ON trials is −0.52 for RISP and −0.61 for LIPS. Its correlation with
the signed score is 0.84 and 0.86, respectively. Median limits fall
with higher PA cutoffs for both situations.

LIPS has a lower median limit at every cutoff despite fewer ON trials
in the primary sample (median 588 versus 869). The greater number of
negative LIPS scores can tighten its conditional positive tail.
The observed distributions reflect both sample sizes and observed
differences, so the lower LIPS median does not isolate an advantage
in precision at a common effect size.

At near-zero significance, more eligible observations yield tighter
constraints. For a strongly negative observation the conditional
positive tail can be particularly narrow even when very little
posterior mass supports a positive effect. The positive probability
and the upper limit describe different aspects of the posterior and
should be read together. The limits are Bayesian credible limits
under the model and priors, with no frequentist coverage guarantee.

The independent-binomial likelihood assumes a fixed hit probability
within each player's ON and OFF trials. Pooling across seasons,
opponents, parks, and game states can conceal changing probabilities
and dependencies between trials. RISP and LIPS may overlap, so the
separate marginal limits describe different contrasts without
establishing independent effects. Career-aggregated observational
data cannot establish persistent clutch skill or a causal effect.

## Figures

- [Representative posterior densities and limits](../../Results/Upper_Limits/figures/posterior_examples.png)
- [RISP and LIPS upper-limit distributions](../../Results/Upper_Limits/figures/upper_limit_distributions.png)
- [Upper limit versus ON eligible trials](../../Results/Upper_Limits/figures/upper_limit_vs_trials.png)
- [Upper limit versus signed binomial score](../../Results/Upper_Limits/figures/upper_limit_vs_score.png)
- [Positive-nondetection limits across PA cutoffs](../../Results/Upper_Limits/figures/upper_limits_by_cutoff.png)

The posterior figure plots the full difference density. The shaded
region from zero to the upper limit contains 95% of the positive-side
mass.

## Reproduction

Run from the repository root after installing requirements.

```bash
python Script/analyze_upper_limits.py
python -m unittest discover -s tests
```

[Player results and diagnostics](../../Results/Upper_Limits/players.csv) ·
[Population summaries and rank correlations](../../Results/Upper_Limits/population_summary.csv) ·
[Representative players](../../Results/Upper_Limits/representative_players.csv) ·
[Numerical validation](../../Results/Upper_Limits/validation.csv)
