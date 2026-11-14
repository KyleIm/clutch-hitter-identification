# Step 3.1 — Weighted ON/OFF preparation

## Fixed batting outcome weights

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

## Retrosheet outcomes

| Category | Retrosheet events |
|---|---|
| Zero | Field out, force out, double play, grounded into double play, fielder's choice out, strikeout, strikeout double play, sacrifice fly, field error, fielder's choice |
| Unintentional walk | walk |
| Hit by pitch | hit_by_pitch |
| Single | single, regardless of hit location |
| Double | double |
| Triple | triple |
| Home run | home_run |
| Excluded | Intentional walk, sacrifice bunt, catcher interference |

The script reuses the Step 1 RISP and LIPS flags. For each situation, the
seven category counts sum to eligible trials for each ON/OFF group.
The eligible trials and exclusions reconcile to total PA. Removing
unintentional walks and hit-by-pitches recovers the prior binomial trial
counts and the four hit categories reproduce the original success totals.
## Coverage

The 28 seasons contain 5,019,958 eligible PA and 63,701 excluded PA in
each comparison. Weighted differences are available for 4,915 of 5,716
players in RISP and 4,113 in LIPS. Every hitter at 1,000, 2,000 and 3,000
PA has eligible trials on both sides in both comparisons
(1,343, 861 and 595 hitters, respectively).

- [RISP counts](../../Results/Weighted_ON_OFF/risp_player_counts.csv)
- [LIPS counts](../../Results/Weighted_ON_OFF/lips_player_counts.csv)
- [Coverage by cutoff](../../Results/Weighted_ON_OFF/coverage.csv)
- [Fixed weights](../../Results/Weighted_ON_OFF/fixed_weights.csv)

## Reproduction

```bash
python Script/prepare_weighted_on_off.py
python -m unittest discover -s tests
```

The script applies the fixed coefficients and writes the weights, player counts,
weighted means and differences, and coverage to the results directory.
