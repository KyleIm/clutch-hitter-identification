"""Build a player WPA and Clutch benchmark from saved Baseball-Reference season pages."""
import argparse
from html.parser import HTMLParser
from pathlib import Path
import re

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "Data" / "BaseballReference"
YEARS = range(1998, 2026)
TABLE = "players_win_probability_batting"
FIELDS = {
    "player": "bbref_name", "team_ID": "team", "PA": "bbref_pa",
    "wpa_plays": "plays", "wpa_bat": "wpa", "leverage_index_avg": "ali",
    "wpa_li_bat": "wpa_li", "wpa_clutch": "season_clutch",
}


class PlayerTable(HTMLParser):
    def __init__(self, table=TABLE, fields=FIELDS):
        super().__init__()
        self.table = table
        self.fields = fields
        self.in_table = False
        self.row = {}
        self.field = None
        self.rows = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "table" and attrs.get("id") == self.table:
            self.in_table = True
        if not self.in_table:
            return
        if tag == "tr":
            self.row = {"partial": "partial_table" in attrs.get("class", "").split()}
        if tag in ("td", "th"):
            self.field = self.fields.get(attrs.get("data-stat"))
            if self.field:
                self.row[self.field] = ""
            if self.field == "bbref_name":
                self.row["bbref_id"] = attrs.get("data-append-csv")

    def handle_data(self, data):
        if self.in_table and self.field:
            self.row[self.field] += data

    def handle_endtag(self, tag):
        if not self.in_table:
            return
        if tag in ("td", "th"):
            self.field = None
        if tag == "tr" and self.row.get("bbref_id"):
            self.rows.append({key: value.strip() if isinstance(value, str) else value for key, value in self.row.items()})
        if tag == "table":
            self.in_table = False


def read_year(path, year):
    page = path.read_text(encoding="utf-8")
    if f"<title>{year} Major League Baseball Win Probability" not in page:
        raise ValueError(f"Unexpected season or page at {path}")
    # Older season pages can embed the player table in an HTML comment.
    table = re.search(r'<table\b[^>]*\bid="players_win_probability_batting"[^>]*>.*?</table>', page, re.S)
    if table is None:
        raise ValueError(f"Player table not found in {path}")
    parser = PlayerTable()
    parser.feed(table.group())
    raw = pd.DataFrame(parser.rows)
    if len(raw) < 500 or not {*FIELDS.values(), "bbref_id"}.issubset(raw.columns):
        raise ValueError(f"Missing or incomplete player table in {path}")
    players = raw.loc[~raw.partial].drop(columns="partial").copy()
    if not players.bbref_id.is_unique or players.bbref_id.nunique() != raw.bbref_id.nunique():
        raise ValueError(f"Duplicate player without exactly one season total in {path}")
    for col in ("bbref_pa", "plays", "wpa", "ali", "wpa_li", "season_clutch"):
        players[col] = pd.to_numeric(players[col].replace("", pd.NA), errors="raise")
    players.insert(0, "season", year)
    return players


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("html_dir", type=Path, help="Directory containing 1998.html through 2025.html")
    cli.add_argument("--output-dir", type=Path, default=DATA)
    args = cli.parse_args()
    mapping = pd.read_csv(DATA / "player_id_mapping.csv", dtype={"bbref_id": "string"})
    if len(mapping) != 5716 or not mapping.bbref_id.is_unique or not mapping.batter.is_unique:
        raise ValueError("Unexpected Chadwick crosswalk")
    seasons = []
    expected = []
    for year in YEARS:
        seasons.append(read_year(args.html_dir / f"{year}.html", year))
        compact = ROOT / "Data" / "Retrosheet" / "Compact" / f"mlb_{year}_plate_appearances_compact.csv"
        players = pd.read_csv(compact, usecols=["batter"]).batter.value_counts()
        expected.append(players.rename("retrosheet_season_pa").reset_index().assign(season=year))
    source = pd.concat(seasons, ignore_index=True)
    reference = pd.concat(expected, ignore_index=True).merge(
        mapping[["batter", "bbref_id"]], on="batter", validate="many_to_one",
    )
    if reference.retrosheet_season_pa.sum() != mapping.total_pa.sum():
        raise ValueError("Retrosheet season PA do not sum to career PA")
    aligned = reference.merge(
        source, on=["bbref_id", "season"], how="outer", validate="one_to_one", indicator=True,
    )
    invalid_clutch = (
        aligned[["wpa", "wpa_li", "ali", "plays"]].isna().any(axis=1)
        | aligned.plays.le(0) | aligned.ali.lt(0)
    )
    counts = aligned.assign(
        incomplete_clutch_season=invalid_clutch,
        leverage_sum=aligned.ali * aligned.plays,
        missing_expected_wpa=aligned.retrosheet_season_pa.notna() & aligned.wpa.isna(),
    ).groupby("bbref_id").agg(
        bbref_pa=("bbref_pa", lambda values: values.sum(min_count=1)),
        observed_wpa=("wpa", lambda values: values.sum(min_count=1)),
        period_wpa_li=("wpa_li", lambda values: values.sum(min_count=1)),
        period_plays=("plays", lambda values: values.sum(min_count=1)),
        leverage_sum=("leverage_sum", lambda values: values.sum(min_count=1)),
        incomplete_clutch_seasons=("incomplete_clutch_season", "sum"),
        seasons_with_wpa=("wpa", "count"),
        missing_expected_wpa=("missing_expected_wpa", "sum"),
    )
    matched = mapping.join(counts, on="bbref_id", validate="one_to_one")
    matched["period_wpa"] = matched.observed_wpa.where(matched.missing_expected_wpa.eq(0))
    complete = matched.incomplete_clutch_seasons.eq(0)
    matched["period_wpa_li"] = matched.period_wpa_li.where(complete)
    matched["period_ali"] = matched.pop("leverage_sum").div(
        matched.period_plays.where(complete & matched.period_plays.gt(0))
    )
    matched["period_clutch_estimate"] = (
        matched.period_wpa.div(matched.period_ali.where(matched.period_ali.gt(0)))
        - matched.period_wpa_li
    )
    matched["pa_difference_bbref_minus_retrosheet"] = (
        matched.bbref_pa - matched.total_pa
    )

    out = args.output_dir
    out.mkdir(parents=True, exist_ok=True)
    source.to_csv(out / "bbref_1998_2025_player_seasons.csv", index=False)
    matched.to_csv(out / "bbref_1998_2025_wpa_matched.csv", index=False)
    print(f"{source.season.nunique()} seasons, {len(source)} player-season rows, {source.bbref_id.nunique()} source IDs")
    print(f"Missing source rows for Retrosheet player-seasons: {aligned._merge.eq('left_only').sum()}")
    print(f"Source player-season rows with missing WPA: {source.wpa.isna().sum()}")
    for cutoff in (0, 1000, 2000, 3000):
        sample = matched[matched.total_pa.ge(cutoff)]
        delta = sample.pa_difference_bbref_minus_retrosheet.dropna()
        print(f"PA >= {cutoff}: WPA {sample.period_wpa.count()}/{len(sample)}; "
              f"Clutch {sample.period_clutch_estimate.count()}/{len(sample)}; "
              f"PA differences {delta.ne(0).sum()}/{len(delta)} "
              f"(range {delta.min()} to {delta.max()})")


if __name__ == "__main__":
    main()
