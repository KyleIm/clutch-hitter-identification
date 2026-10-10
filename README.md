# A Method for Identifying Clutch Hitters

Classic approaches to identifying clutch hitters include Cramer's expected PWA framework and Ruane's direct RISP vs. non-RISP comparison. Ruane's RISP definition could later be replaced by LIPS, or supplemented with a LIPS-based analysis. This project explores whether ideas from astrophysical ON/OFF analysis can be used to statistically improve Ruane-style within-player comparisons.

In astrophysical counting experiments, the number of events observed in an ON region, where a source is expected to be present, is compared against the number of events observed in an OFF region, which serves as a background or control region. When the two regions differ in size, observation time, or effective exposure, an exposure ratio is used to account for that imbalance. Li-Ma significance is one representative method built for this kind of problem. Translating the broader ON/OFF philosophy to baseball suggests a way to compare each player's own clutch and non-clutch performance directly, rather than relying primarily on how that player performed relative to the entire league.

The current implementation replaces the original Poisson Li-Ma formula with a binomial ON/OFF likelihood-ratio statistic. This should be understood as a Li-Ma-style ON/OFF adaptation for two binomial samples, not as the original Li-Ma significance itself. The statistic compares each player's clutch and non-clutch success probabilities while accounting for the number of observed successes and failures in both samples.

## Repository Layout

```text
.
├── Data/
│   ├── Retrosheet/Compact/              # 1998-2025 compact MLB PA extracts
│   ├── Retrosheet/Raw/                  # Local Retrosheet zip downloads, ignored by git
│   ├── mlb_1998_2025_RISP_sample_counts.csv
│   └── mlb_2025_RISP_sample_counts.csv
├── Script/
│   ├── download_retrosheet_csv.py
│   ├── build_retrosheet_pa_compact.py   # Build compact PA data from Retrosheet event files
│   ├── build_retrosheet_pa_compact_range.py
│   ├── build_league_RISP_sample_counts.py
│   ├── lima_histogram_RISP_sample.py    # Core RISP labeling and binomial ON/OFF S helpers
│   └── plot_RISP_histogram.py
├── cle_2026_07_plate_appearances_compact.csv
└── cle_2026_07_statcast_pitches_raw.csv
```

## Method

The working derivation for the binomial ON/OFF likelihood-ratio statistic is saved in [`docs/binomial_on_off_likelihood_derivation.md`](docs/binomial_on_off_likelihood_derivation.md).

For each hitter:

- `n`: plate appearances with a runner on second and/or third
- `b`: plate appearances without RISP
- `n_trials`: RISP successes plus failures, excluding walks, hit by pitch, catcher interference, and sacrifice bunts
- `b_trials`: non-RISP successes plus failures under the same event filter
- `n_rate`: success rate in RISP plate appearances
- `b_rate`: success rate in non-RISP plate appearances
- `S`: signed binomial ON/OFF likelihood-ratio statistic comparing `n_rate` with `b_rate`

Success events currently include singles, doubles, triples, and home runs. Walks, hit by pitch, catcher interference, and sacrifice bunts are excluded from the success-rate denominator.

## Reproduce

Create an environment and install dependencies:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Download Retrosheet parsed CSV zip files:

```bash
python Script/download_retrosheet_csv.py --start-year 1998 --end-year 2025
```

Build compact plate-appearance files:

```bash
python Script/build_retrosheet_pa_compact_range.py --start-year 1998 --end-year 2025
```

Build the 1998-2025 player summary:

```bash
python Script/build_league_RISP_sample_counts.py \
  --input-glob 'Data/Retrosheet/Compact/mlb_*_plate_appearances_compact.csv' \
  --output Data/mlb_1998_2025_RISP_sample_counts.csv
```

Show the histogram:

```bash
python Script/plot_RISP_histogram.py
```

## Current Snapshot

The histograms below show career-level RISP and LIPS signed binomial ON/OFF significance for 1998-2025 hitters with at least 2000 career plate appearances. The RISP distribution remains relatively close to centered, while the LIPS distribution is shifted substantially negative. This shift is plausibly related to the fact that LIPS plate appearances occur in late and close game states, where hitters are more likely to face high-leverage relief pitchers. The league-wide LIPS/non-LIPS baseline should therefore be evaluated before interpreting player-level signs as clutch effects.

![1998-2025 RISP Binomial ON/OFF S Distribution](binomial_onoff_risp_histogram_1998_2025_pa2000.png)

![1998-2025 LIPS Binomial ON/OFF S Distribution](binomial_onoff_lips_histogram_1998_2025_pa2000.png)

## Planned Analyses

The roadmap is organized around career-level analyses. The immediate priorities are to validate the existing marginal binomial ON/OFF statistics, investigate RISP/LIPS distributional behavior and league-wide baselines, develop a joint RISP–LIPS likelihood-ratio model, evaluate whether a directional joint clutch index can be statistically justified, compare the resulting measures with established sabermetric approaches, and then pursue upper-limit and secondary extensions.

### Statistical validation and sensitivity analysis

The current ON/OFF statistic uses a binomial likelihood for two independent success/failure samples and is mathematically equivalent to a standard two-proportion likelihood-ratio, or G, test. The Li-Ma connection is methodological motivation from the ON/OFF likelihood-ratio framework; the likelihood used here is binomial rather than Poisson.

- Validate the binomial ON/OFF statistic against the standard two-proportion likelihood-ratio (G) test.
- Perform Monte Carlo null simulations using observed ON/OFF trial counts to evaluate the calibration of the signed significance statistic.
- Conduct PA cutoff sensitivity analyses using career PA thresholds of 1000, 2000, and 3000. The current primary threshold is 2000 PA.
- Compare the mean, median, standard deviation, skewness, and positive/negative tail fractions at thresholds such as `|S| > 2` and `|S| > 3`.
- Optionally examine the robustness of career-level significance using leave-one-season-out analyses.
- Distinguish this robustness check from year-to-year repeatability of player-specific clutch skill, which is a separate question.
- Address multiple testing across players using an appropriate method, such as false discovery rate control or population-level null simulations.

### RISP and LIPS cross-validation

RISP and LIPS are separate clutch situation definitions. They are analyzed with the same binomial ON/OFF framework, but their baseline distributions need not be the same. For 1998-2025 career-level results with career PA >= 2000, the current player sample contains 861 hitters.

| Statistic | RISP | LIPS |
|---|---:|---:|
| Mean | -0.212 | -0.989 |
| Standard deviation | 1.051 | 1.079 |

- Calculate Pearson and Spearman correlations between player-level RISP and LIPS signed significance.
- Generate a player-level scatter plot comparing the two statistics.
- Compare the overlap of top-performing and bottom-performing players, including the top and bottom 5%.
- Compare empirical standardized scores within each distribution, while explicitly distinguishing these relative scores from statistical detection significance.
- Compare raw ON/OFF effect sizes, defined as batting-average differences, for RISP and LIPS.
- Quantify league-wide RISP/non-RISP and LIPS/non-LIPS baseline differences and investigate their effects on the significance distributions.
- Account for overlap between RISP and LIPS plate appearances when interpreting correlations. Null simulations or permutation methods should be used to evaluate whether observed agreement exceeds what would be expected from overlapping samples alone.
- Avoid automatically recentering the signed significance distributions and reinterpreting recentered values as statistical significance.

### Joint RISP–LIPS Likelihood-Ratio Analysis

The current implementation computes two separate career-level signed binomial ON/OFF likelihood-ratio statistics: `S_R` for RISP versus non-RISP batting performance and `S_L` for LIPS versus non-LIPS batting performance. A combined measure such as

$$
C_{\mathrm{new}} = aS_R + bS_L
$$

would require defensible weights and must account for overlapping observations and statistical dependence between the two situation definitions. Rather than assigning arbitrary weights or fitting them directly to an existing sabermetric metric, the next methodological objective is to investigate whether a combined clutch measure can be derived from a joint likelihood model. FanGraphs Clutch should be reserved for subsequent external comparison, not used as the primary training target for determining the new index.

Batting observations can be partitioned into four mutually exclusive categories according to RISP and LIPS indicators:

| Category | RISP | LIPS |
|---|---|---|
| A | No | No |
| B | Yes | No |
| C | No | Yes |
| D | Yes | Yes |

For each category, hits and eligible batting trials should be calculated using the same event-filtering rules used in the current marginal analyses. The number of hits in category `j` can then be modeled as

$$
H_j \sim \mathrm{Binomial}(N_j, p_j).
$$

A binomial logistic model can represent conditional RISP and LIPS effects:

$$
\mathrm{logit}(p_j)
=
\beta_0+\beta_R I_{\mathrm{RISP},j}
+\beta_L I_{\mathrm{LIPS},j}.
$$

The coefficients represent conditional situational effects on batting success probability. The joint null hypothesis is

$$
H_0:\beta_R=\beta_L=0.
$$

The likelihood-ratio statistic is

$$
TS_{\mathrm{joint}}
=
2\left(\ln\mathcal L_{\mathrm{alternative}}
-\ln\mathcal L_{\mathrm{null}}\right).
$$

Under standard regularity conditions, the asymptotic null distribution is chi-square with two degrees of freedom. This is an established likelihood-ratio methodology applied to a joint baseball situational model, not a newly invented statistical test.

- Implement the four-category RISP/LIPS partition.
- Verify that every eligible batting observation is assigned to exactly one category.
- Fit the joint binomial logistic model for each eligible player.
- Calculate the joint likelihood-ratio statistic and estimate the RISP/LIPS coefficients.
- Evaluate finite-sample calibration using Monte Carlo simulations.
- Investigate whether an interaction term between RISP and LIPS is necessary.
- Compare the joint results with the existing marginal RISP and LIPS significance statistics.
- Examine league-wide situational effects and whether an adjusted null model is appropriate.
- Check player-level sample sizes and potential separation problems before assuming the four category probabilities can be estimated reliably.

### Proposed Joint Clutch Index

The project also aims to investigate a directional clutch index derived from the joint likelihood framework. This requires separating two related but distinct objects:

1. The joint likelihood-ratio statistic, which measures evidence against the null hypothesis that both situational effects are zero.
2. A directional clutch index, which would be intended to distinguish positive from negative situational batting performance.

The ordinary two-degree-of-freedom joint likelihood-ratio statistic is nonnegative and does not provide a natural sign. Constructing a signed index therefore requires an additional, explicitly justified definition of the direction of the combined effect.

Potential approaches for future investigation include:

- A prespecified linear contrast of the fitted RISP and LIPS coefficients.
- A constrained common-effect model, provided its assumptions can be justified.
- A covariance-aware directional statistic derived from the joint model.

No final directional index has been selected or validated. Any proposed index must be evaluated for statistical interpretation, null-distribution calibration, sensitivity to sample size, stability under different PA cutoffs, dependence on league-wide situational baselines, and potential double-counting of overlapping RISP/LIPS observations. A new directional index should not be labeled as a Z-score or statistical significance unless its calibration supports that interpretation.

### Comparison with established clutch metrics

This analysis should be compared with existing sabermetric clutch measurements, especially FanGraphs Clutch and Ruane's RISP/non-RISP comparison using the difference in BPS (`BA + SLG`). FanGraphs Clutch is defined as

$$
Clutch_{\mathrm{FG}}
=
\frac{WPA}{pLI}-WPA/LI.
$$

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
- Discuss differences in the underlying estimands: statistical evidence for batting-average changes versus situational run or win contributions.
- Do not treat the unsigned joint likelihood-ratio statistic as directly equivalent to signed FanGraphs Clutch. If the unsigned statistic is compared with the magnitude of FanGraphs Clutch, the limitations of that comparison should be stated explicitly.
- Avoid claiming that the proposed framework is superior solely because it produces a likelihood-ratio significance.

### Upper limits

- Set upper limits for player-specific clutch effects after the null calibration and league-wide situational baseline checks are complete.

## Data Notes

The compact 1998-2025 plate-appearance extracts are derived from Retrosheet parsed play-by-play CSV files. Retrosheet terms and attribution should be followed for any public use of their source data.
