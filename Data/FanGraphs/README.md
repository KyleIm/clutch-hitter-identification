# FanGraphs season wRC+

## Step 3 extension · wRC+

On November 15, 2026, the 1998–2025 aggregate leaderboard
returned MEMBERSHIP_REQUIRED__10YR. The single-season leaderboard
responded for every year from 1998 through 2025. The extension uses
one row per player for each regular season, both leagues, all positions,
all teams, no team or season splits, and a zero-PA minimum.

[Example season leaderboard](https://www.fangraphs.com/leaders/major-league?pos=all&stats=bat&lg=all&qual=0&type=8&season=1998&season1=1998&ind=0) ·
[FanGraphs wRC+ definition](https://library.fangraphs.com/offense/wrc/)

The local wrc-YEAR.csv inputs contain playerid, Season, SeasonMin,
SeasonMax, PA and wRC+ from the leaderboard response. The query path
is /api/leaders/major-league/data on www.fangraphs.com with the same
filter parameters as the leaderboard and pageitems=2000 and pagenum=1.
Check totalCount against the returned row count and keep the native
FanGraphs player ID. The retrieved files passed the count and season
checks for all 28 seasons.

The period value is a PA-weighted average of season wRC+, which may
differ from an official period wRC+ computed from pooled inputs. The
existing Chadwick crosswalk supplies FanGraphs IDs. The period file
compares source PA with Retrosheet PA and leaves a period estimate
blank if no valid full-period set of seasons can be matched. See the
[Step 3 report](../../docs/analysis/03_external_benchmark.md#dependence-on-overall-batting-performance)
for the preparation and analysis commands. Source tables and matched
player-level indexes are local research inputs. Review the
[FanGraphs terms](https://www.fangraphs.com/about/terms-of-service)
before any redistribution.

The player ID crosswalk derives from the [Chadwick Bureau Register](https://github.com/chadwickbureau/register)
at revision ba48ce101349a2156c7a5420f54d13e8ef3a4256 under the
[Open Data Commons Attribution License 1.0](https://opendatacommons.org/licenses/by/1-0/).