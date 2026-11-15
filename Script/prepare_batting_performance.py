"""Build period batting indexes from locally saved regular-season source tables."""
import argparse
from pathlib import Path
import re

import numpy as np
import pandas as pd

from aggregate_bbref_wpa import DATA, ROOT, YEARS, PlayerTable

TABLE = "players_standard_batting"
FIELDS = {"name_display": "bbref_name", "b_pa": "pa", "b_onbase_plus_slugging_plus": "ops_plus"}
FG = ROOT / "Data/FanGraphs"


def read_ops(path, year):
    page = path.read_text(encoding="utf-8-sig")
    table = re.search(r'<table\b[^>]*\bid="players_standard_batting"[^>]*>.*?</table>', page, re.S)
    if f"<title>{year} " not in page or table is None:
        raise ValueError(f"Expected {year} regular-season batting table in {path}")
    parser = PlayerTable(TABLE, FIELDS)
    parser.feed(table.group())
    source = pd.DataFrame(parser.rows)
    rows = source.loc[~source.partial, ["bbref_id", "pa", "ops_plus"]].copy()
    if rows.bbref_id.nunique() != source.bbref_id.nunique():
        raise ValueError(f"Missing season totals in {path}")
    return rows.assign(season=year)


def read_wrc(path, year):
    rows = pd.read_csv(path, dtype={"playerid": "string"})
    if not rows[["Season", "SeasonMin", "SeasonMax"]].eq(year).all().all():
        raise ValueError(f"Unexpected season scope in {path}")
    return rows[["playerid", "PA", "wRC+"]].rename(
        columns={"playerid": "fangraphs_id", "PA": "pa", "wRC+": "wrc_plus"}).assign(season=year)


def checked_seasons(frames, source_id, metric):
    for rows in frames:
        if len(rows) < 500 or rows[source_id].isna().any() or not rows[source_id].is_unique:
            raise ValueError(f"Incomplete or duplicate {source_id} season")
    data = pd.concat(frames, ignore_index=True)
    data["pa"] = pd.to_numeric(data.pa, errors="raise")
    data[metric] = pd.to_numeric(data[metric].replace("", np.nan), errors="raise")
    if not np.isfinite(data.pa).all() or data.pa.lt(0).any() or data.pa.mod(1).ne(0).any():
        raise ValueError(f"Invalid {source_id} plate appearances")
    if np.isinf(data[metric]).any():
        raise ValueError(f"Invalid {metric} values")
    return data


def period_index(expected, mapping, source, source_id, metric):
    linked = expected.merge(mapping[["batter", source_id]], on="batter", validate="many_to_one")
    linked = linked.merge(source, on=[source_id, "season"], how="left", validate="many_to_one", indicator=True)
    # A zero-PA season carries no weight. A missing expected row or an
    # undefined metric with positive PA invalidates the player's period index.
    linked["missing_row"] = linked._merge.ne("both")
    linked["missing_metric"] = linked.pa.gt(0) & linked[metric].isna()
    linked["weighted"] = (linked.pa * linked[metric]).where(linked.pa.ne(0), 0)
    grouped = linked.groupby("batter").agg(
        expected_seasons=("season", "size"), missing_rows=("missing_row", "sum"),
        missing_metric_seasons=("missing_metric", "sum"),
        source_pa=("pa", lambda s: s.sum(min_count=1)), numerator=("weighted", "sum"),
        retrospective_pa=("retrosheet_pa", "sum"))
    extra = source.merge(mapping[[source_id, "batter"]].dropna(), on=source_id, validate="many_to_one")
    extra = extra.merge(expected[["batter", "season"]], how="left", on=["batter", "season"], indicator=True)
    extra = extra.loc[extra._merge.eq("left_only") & extra.pa.gt(0)].groupby("batter").size()
    grouped["extra_positive_pa_seasons"] = extra.reindex(grouped.index, fill_value=0)
    valid = grouped[["missing_rows", "missing_metric_seasons", "extra_positive_pa_seasons"]].eq(0).all(axis=1)
    grouped[metric] = grouped.numerator.div(grouped.source_pa.where(valid & grouped.source_pa.gt(0)))
    grouped["pa_difference"] = grouped.source_pa - grouped.retrospective_pa
    return grouped.drop(columns=["numerator", "retrospective_pa"]).add_prefix(f"{metric}_").rename(
        columns={f"{metric}_{metric}": metric}).reset_index()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input_dir", type=Path, help="Contains bb-YEAR.html and wrc-YEAR.csv")
    parser.add_argument("--fangraphs-mapping", type=Path, default=FG / "player_id_mapping.csv")
    args = parser.parse_args()
    expected = pd.concat([
        pd.read_csv(ROOT / "Data/Retrosheet/Compact" / f"mlb_{year}_plate_appearances_compact.csv",
                    usecols=["batter"]).batter.value_counts().rename_axis("batter").reset_index(
                        name="retrosheet_pa").assign(season=year)
        for year in YEARS], ignore_index=True)
    for directory, mapping_path, metric, source_id, frames in (
        (DATA, DATA / "player_id_mapping.csv", "ops_plus", "bbref_id",
         [read_ops(args.input_dir / f"bb-{year}.html", year) for year in YEARS]),
        (FG, args.fangraphs_mapping, "wrc_plus", "fangraphs_id",
         [read_wrc(args.input_dir / f"wrc-{year}.csv", year) for year in YEARS]),
    ):
        mapping = pd.read_csv(mapping_path, dtype={source_id: "string"})
        if set(mapping.batter) != set(expected.batter) or not mapping.batter.is_unique or not mapping[source_id].dropna().is_unique:
            raise ValueError(f"Unexpected crosswalk: {mapping_path}")
        source = checked_seasons(frames, source_id, metric)
        source.to_csv(directory / f"{metric}_1998_2025_seasons.csv", index=False)
        period = period_index(expected, mapping, source, source_id, metric)
        period = period.merge(mapping[["batter", source_id]], validate="one_to_one", on="batter")
        period.to_csv(directory / f"{metric}_1998_2025_period.csv", index=False)
        print(metric, len(source), "season rows;", period[metric].count(), "valid period values")


if __name__ == "__main__":
    main()
