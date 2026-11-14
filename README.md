# A Method for Identifying Clutch Hitters

## Project Overview

How does a hitter’s performance change in different game situations? This
project adapts the astrophysical ON/OFF framework to compare each hitter’s
hit rate in a defined situation with their hit rate in all other situations.

## Dataset

The 1998–2025 Retrosheet play-by-play extracts cover **5,716 hitters** and
**4,569,453 eligible batting trials**. The primary analysis includes 861 hitters
with at least 2,000 career plate appearances (PA).

- **RISP (runners in scoring position)** means a runner is on second or third before the final pitch.
- **LIPS (late-inning pressure situations)** means the seventh inning or later, with the batting team ahead by one, tied, or trailing by up to three. A four-run deficit also qualifies if the bases are loaded at the start of the PA.

## Statistical Methodology

The signed binomial ON/OFF score is the square root of the standard
two-proportion likelihood-ratio G statistic, with the sign of the ON-minus-OFF
hit-rate difference. It uses the astrophysical ON/OFF comparison with a
binomial likelihood for hits and failures. See the [mathematical derivation](docs/methodology/binomial_on_off.md).

## Key Findings

LIPS scores shifted lower than RISP scores at all three PA cutoffs. The signed
scores and raw hit-rate differences showed near-zero correlations. In 10,000
simulations that preserved shared batting trials, the observed score
correlations fell within the central 95% null intervals.

| Result for hitters with ≥ 2,000 PA | Estimate |
|---|---:|
| Mean signed score, RISP / LIPS | −0.212 / −0.989 |
| Observed score correlation, Pearson / Spearman | 0.0043 / 0.0109 |
| Overlap-aware null mean, Pearson / Spearman | −0.0018 / −0.0016 |
| One-sided p-value for positive excess, Pearson / Spearman | 0.432 / 0.359 |

![RISP and LIPS score distributions by career PA cutoff](Results/RISP_LIPS/figures/boxplot.png)

Against Baseball-Reference Clutch at 2,000 PA, Pearson r was 0.276 for
RISP and 0.354 for LIPS. The one-sided Williams test gave p = 0.041, and
the two-sided bootstrap 95% interval for the difference was [−0.013, 0.167].
[Step 2 results](docs/analysis/02_external_benchmark.md)

At 2,000 PA, combining RISP and LIPS yielded Pearson r = 0.448 and
R² = 0.201 in sample. Five-fold validation yielded r = 0.443 and R² =
0.197, compared with R² = 0.123 for LIPS alone.
[Regression extension](docs/analysis/02_external_benchmark.md#regression-extension)

## Analysis

| Analysis | Description | Status |
|---|---|---|
| [Baseline Analysis](docs/analysis/00_baseline_analysis.md) | Binomial ON/OFF statistics and significance distributions | Completed |
| [Step 1](docs/analysis/01_risp_lips_correlation.md) | RISP–LIPS EDA, correlation analysis, and hypothesis testing | Completed |
| [Step 2](docs/analysis/02_external_benchmark.md) | Baseball-Reference Clutch and WPA benchmark | Completed |
| [Step 3.1](docs/analysis/03_weighted_on_off.md) | Weighted ON/OFF outcome preparation and weight calibration | Counts ready, weights pending |

## Reproduction

From the repository root, create a virtual environment with
`python -m venv .venv` and activate it before running the following.

```bash
python -m pip install -r requirements.txt
python Script/analyze_risp_lips.py
python Script/analyze_external_benchmark.py
python Script/analyze_clutch_regression.py
python Script/prepare_weighted_on_off.py
python -m unittest discover -s tests
```

The script uses the included data. See the [baseline reproduction commands](docs/analysis/00_baseline_analysis.md#reproduction)
to rebuild the marginal summaries and histograms.

The Baseball-Reference benchmark sums published season WPA and estimates
period Clutch from season Win Probability statistics over 1998–2025.
See the [data README](Data/BaseballReference/README.md) for the aggregation
method, coverage, and reproduction command.

## Repository Structure

```text
.
├── README.md
├── AGENTS.md
├── Data/
├── Script/
├── Results/
│   ├── RISP_LIPS/
│   └── External_Benchmark/
├── docs/
│   ├── methodology/binomial_on_off.md
│   ├── analysis/
│   │   ├── 00_baseline_analysis.md
│   │   ├── 01_risp_lips_correlation.md
│   │   └── 02_external_benchmark.md
│   └── roadmap.md
└── tests/
```

## Roadmap

Step 3 develops weighted batting production for RISP and LIPS. The framework
uses fixed outcome weights across 1998–2025, so a home run in 1998 will
receive the same weight as one in 2025 regardless of the offensive environment.
Outcome counts are available while source coefficients remain pending.
[Step 3.1 methodology](docs/analysis/03_weighted_on_off.md) · [Roadmap](docs/roadmap.md)

## Data Sources and Attribution

The compact extracts are derived from Retrosheet’s parsed play-by-play CSV
files. Follow Retrosheet’s attribution and data-use terms when redistributing
the data or derived products. [Retrosheet CSV downloads and notices](https://retrosheet.org/downloads/csvdownloads.html).

> The information used here was obtained free of charge from and is copyrighted by Retrosheet.
