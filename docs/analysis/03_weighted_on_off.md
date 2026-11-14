# Step 3.1 — Weighted ON/OFF preparation

## Weight sources and coverage

Baseball-Reference describes league-season rOBA coefficients and adjustments
for pitcher batting, reaching on error, and infield versus outfield hits.
Its worked example gives basic MLB wOBA coefficients for 2010. The example
covers one season and uses a different model from rOBA. The reviewed
documentation and public data listings did not provide a fixed set for
1998–2025 or a complete table of 56 AL/NL league-season coefficients.
[Baseball-Reference wRAA methodology](https://www.baseball-reference.com/about/war_explained_wraa.shtml) ·
[Baseball-Reference position player WAR methodology](https://www.baseball-reference.com/about/war_explained_position.shtml)

The source audit records the published example and the zero-outcome rule.
The production weights remain pending. The output leaves weighted means
and differences blank until a documented coefficient set is available.
For annual inputs, the script takes the arithmetic mean of each outcome
coefficient across the 56 AL/NL league-seasons, giving each equal weight.
The supplied single coefficient should represent aggregate singles.

The weighted framework uses fixed batting outcome weights across the
entire 1998–2025 analysis period. A home run in 1998 receives the same
weight as one in 2025 regardless of the offensive environment.
The numerical home-run weight remains pending.

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
With coefficients supplied, each side's weighted mean is its sum of
weighted category counts divided by eligible trials. The raw difference
subtracts the OFF mean from the ON mean.

## Coverage

The 28 seasons contain 5,019,958 eligible PA and 63,701 excluded PA in
each comparison. Both groups have eligible trials for 4,915 of 5,716
players in RISP and 4,113 in LIPS. Every hitter at 1,000, 2,000 and 3,000
PA has eligible trials on both sides in both comparisons
(1,343, 861 and 595 hitters, respectively).

- [RISP counts](../../Results/Weighted_ON_OFF/risp_player_counts.csv)
- [LIPS counts](../../Results/Weighted_ON_OFF/lips_player_counts.csv)
- [Coverage by cutoff](../../Results/Weighted_ON_OFF/coverage.csv)
- [Source audit](../../Results/Weighted_ON_OFF/weight_source_audit.csv)

## Reproduction

```bash
python Script/prepare_weighted_on_off.py
python -m unittest discover -s tests
```

The optional `--weights` CSV takes `kind,season,league,source_url,zero,ubb,hbp,single,double,triple,home_run`.
Use one `representative_1998_2025` row with a verified representative
source, or 56 `league_season` rows covering 1998–2025 for both AL and NL.
A weighted run also writes `fixed_weights.csv`.
