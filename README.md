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

### Weighted ON/OFF framework

The original binomial model gives every hit a value of 1 and excludes
walks and hit-by-pitches. The weighted framework includes unintentional
walks and hit-by-pitches and gives each hit type its own weight.

A representative set of Baseball-Reference batting outcome weights for
1998–2025 could not be obtained. The study adopts the fixed weights from
FanGraphs Basic wOBA and retains Baseball-Reference Clutch as the external
benchmark.

| Batting outcome | Original binomial weight | New fixed weight |
|---|---:|---:|
| Out / ROE | 0 | 0.00 |
| Unintentional BB | Excluded | 0.70 |
| HBP | Excluded | 0.70 |
| Single | 1 | 0.90 |
| Double | 1 | 1.25 |
| Triple | 1 | 1.60 |
| Home run | 1 | 2.00 |

Jeff Zimmerman (2015), [Basic wOBA Equation](https://blogs.fangraphs.com/instagraphs/basic-woba-equation/), FanGraphs, May 14, 2015.
Zimmerman reported R² = 0.986 between Basic wOBA and actual wOBA for
players with more than 200 plate appearances since 1980, supporting the
use of fixed coefficients across seasons.

The framework adapts Basic wOBA by using its published coefficients with
the project's own eligible PA definition. Intentional walks, sacrifice
bunts, and catcher interference are excluded. Sacrifice flies and
reaching on error count as zero. All singles receive the published
single weight of 0.90.

For each ON or OFF sample, weighted batting production is

```text
μ = Σᵢ wᵢpᵢ = (Σᵢ wᵢNᵢ)/T
```

Here `Nᵢ` is the outcome count, `T` is the total number of eligible trials,
and `pᵢ = Nᵢ/T`. The raw weighted difference is `μ_ON − μ_OFF`. A group
with zero eligible trials has an undefined mean.

The fixed-weight framework assigns identical values to equivalent batting
outcomes across all seasons. A home run in 1998 and one in 2025 both receive
a weight of 2.00 regardless of differences in the offensive environment.
[Step 3.1 methodology](docs/analysis/03_weighted_on_off.md)

The binomial statistic compares hit probabilities. The weighted multinomial
statistic compares weighted production means across seven outcomes and allows
different ON and OFF distributions under the null. In 100,000 validation
fits there were no optimizer failures. Nominal 5% rejection was 4.57–5.24%
in the five realistic null configurations and 1.63% in the sparse case.
[Multinomial derivation](docs/methodology/multinomial_on_off.md) ·
[Step 3.2 validation](docs/analysis/03_2_weighted_validation.md)

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
| [Step 3.1](docs/analysis/03_weighted_on_off.md) | Fixed weights and weighted ON/OFF batting production | Completed |
| [Step 3.2](docs/analysis/03_2_weighted_validation.md) | Weighted multinomial likelihood and calibration | Completed |

## Reproduction

From the repository root, create a virtual environment with
`python -m venv .venv` and activate it before running the following.

```bash
python -m pip install -r requirements.txt
python Script/analyze_risp_lips.py
python Script/analyze_external_benchmark.py
python Script/analyze_clutch_regression.py
python Script/prepare_weighted_on_off.py
python Script/validate_weighted_on_off.py --simulations 10000
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
│   ├── prepare_weighted_on_off.py
│   ├── multinomial_on_off.py
│   └── validate_weighted_on_off.py
├── Results/
│   ├── RISP_LIPS/
│   ├── External_Benchmark/
│   └── Weighted_ON_OFF/
│       ├── fixed_weights.csv
│       ├── risp_player_counts.csv
│       ├── lips_player_counts.csv
│       ├── coverage.csv
│       └── Validation/
├── docs/
│   ├── methodology/
│   │   ├── binomial_on_off.md
│   │   └── multinomial_on_off.md
│   ├── analysis/
│   │   ├── 00_baseline_analysis.md
│   │   ├── 01_risp_lips_correlation.md
│   │   ├── 02_external_benchmark.md
│   │   ├── 03_weighted_on_off.md
│   │   └── 03_2_weighted_validation.md
│   └── roadmap.md
└── tests/
```

## Roadmap

Step 3.2 validates the weighted statistic. The weighted baseline and
external benchmark comparison are planned. [Roadmap](docs/roadmap.md)

## Data Sources and Attribution

The compact extracts are derived from Retrosheet’s parsed play-by-play CSV
files. Follow Retrosheet’s attribution and data-use terms when redistributing
the data or derived products. [Retrosheet CSV downloads and notices](https://retrosheet.org/downloads/csvdownloads.html).

> The information used here was obtained free of charge from and is copyrighted by Retrosheet.
