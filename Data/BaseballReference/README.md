# Baseball-Reference batting WPA and Clutch benchmark

The 1998–2025 dataset uses the Player Win Probability table from each MLB regular-season batting page. The 28 public pages yielded 25,439 player-season rows after removing partial rows. They cover all 5,716 Retrosheet hitters. The source tables show WPA to one decimal place.

## How period WPA was calculated

For each season, read the Baseball-Reference player ID from the table's CSV identifier. Keep the player-season row and discard rows marked as partial, which can include team stints and league subtotals. For a player who changed teams, the full-season row supplies the total. Require exactly one row per player and season.

Join Baseball-Reference IDs to Retrosheet batter IDs using the [Chadwick Bureau Register](https://github.com/chadwickbureau/register) at revision ba48ce101349a2156c7a5420f54d13e8ef3a4256. The crosswalk uses the [Open Data Commons Attribution License 1.0](https://opendatacommons.org/licenses/by/1-0/).

Period WPA is the sum of the published season WPA values from 1998 through 2025, inclusive. The sum inherits rounding from each season. Every Retrosheet player-season is checked for a source row and a WPA value. When an expected season is missing, the output leaves period WPA blank and keeps any available sum in observed_wpa. Season-level Clutch, aLI and WPA/LI are retained in the season file.

## How period Clutch was estimated

The calculation follows the Baseball-Reference Clutch definition. Sum each player's season WPA and season WPA/LI across 1998–2025. Calculate period aLI by weighting each season's aLI by its published Plays count, then compute period WPA divided by period aLI minus summed WPA/LI. The output column period_clutch_estimate uses this formula with rounded season inputs. [Baseball-Reference Win Expectancy glossary](https://www.baseball-reference.com/about/wpa.shtml)

A missing required input or a zero period aLI leaves the estimate blank. All 54 blank estimates in this run had a zero period aLI based on the displayed season values. The original season Clutch values remain available in the season file, including 182 blank values.

| Retrosheet PA cutoff | Players with period WPA | Players with period Clutch estimate | Players with a PA difference |
|---:|---:|---:|---:|
| All | 5,716 / 5,716 | 5,662 / 5,716 | 169 |
| 1,000 | 1,343 / 1,343 | 1,343 / 1,343 | 144 |
| 2,000 | 861 / 861 | 861 / 861 | 119 |
| 3,000 | 595 / 595 | 595 / 595 | 96 |

Every expected player-season had a source WPA value. Baseball-Reference period PA minus Retrosheet period PA ranged from 0 to +13. The output records the differences without adjusting either source's counts.

## Reproduction

Save each season page as YEAR.html in a local directory. Use the [1998 Player Win Probability page](https://www.baseball-reference.com/leagues/majors/1998-win_probability-batting.shtml) as the URL pattern and replace the year through 2025. The inputs for this run were retrieved on November 13, 2026. Follow the [Sports Reference data use policy](https://www.sports-reference.com/data_use.html) and [request guidance](https://www.sports-reference.com/bot-traffic.html).

```bash
python Script/aggregate_bbref_wpa.py ../bref-seasons
```

The script writes bbref_1998_2025_player_seasons.csv and bbref_1998_2025_wpa_matched.csv here by default. Both generated data files are local and excluded from Git pending verification of redistribution rights.
