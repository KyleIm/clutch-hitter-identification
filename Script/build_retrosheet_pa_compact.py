#!/usr/bin/env python3
import argparse
import csv
import zipfile
from collections import defaultdict
from pathlib import Path


OUTPUT_COLUMNS = [
    "game_date",
    "game_pk",
    "team",
    "player_name",
    "batter",
    "batter_pa_number_this_game",
    "outs_when_up",
    "runner_situation_start",
    "runner_situation_before_final_pitch",
    "runner_situation_changed_during_pa",
    "events",
    "inning",
    "bat_score",
    "fld_score",
]


def runner_situation(row):
    bases = []
    if row.get("br1_pre"):
        bases.append("1B")
    if row.get("br2_pre"):
        bases.append("2B")
    if row.get("br3_pre"):
        bases.append("3B")
    return "+".join(bases) if bases else "empty"


def format_date(yyyymmdd):
    return f"{yyyymmdd[:4]}-{yyyymmdd[4:6]}-{yyyymmdd[6:8]}"


def load_player_names(zip_path, year):
    names = {}
    member = f"{year}allplayers.csv"
    with zipfile.ZipFile(zip_path) as zf, zf.open(member) as fh:
        reader = csv.DictReader((line.decode("utf-8-sig") for line in fh))
        for row in reader:
            names[row["id"]] = f'{row["last"]}, {row["first"]}'
    return names


def retrosheet_event_name(row):
    event = row["event"]
    outs_made = int(row["outs_post"]) > int(row["outs_pre"])

    if row["iw"] == "1":
        return "intent_walk"
    if row["walk"] == "1":
        return "walk"
    if row["hbp"] == "1":
        return "hit_by_pitch"
    if row["xi"] == "1":
        return "catcher_interf"
    if row["hr"] == "1":
        return "home_run"
    if row["triple"] == "1":
        return "triple"
    if row["double"] == "1":
        return "double"
    if row["single"] == "1":
        return "single"
    if row["sh"] == "1":
        return "sac_bunt"
    if row["sf"] == "1":
        return "sac_fly"
    if row["k"] == "1" and row["othdp"] == "1":
        return "strikeout_double_play"
    if row["k"] == "1":
        return "strikeout"
    if row["gdp"] == "1":
        return "grounded_into_double_play"
    if row["othdp"] == "1":
        return "double_play"
    if row["roe"] == "1":
        return "field_error"
    if row["fc"] == "1":
        return "fielders_choice_out" if outs_made else "fielders_choice"
    if event.startswith("FO"):
        return "force_out"
    if outs_made:
        return "field_out"
    return "other"


def bat_and_field_scores(row):
    away_score = int(row["score_v"])
    home_score = int(row["score_h"])
    if row["vis_home"] == "0":
        return away_score, home_score
    return home_score, away_score


def iter_play_rows(zip_path, year):
    member = f"{year}plays.csv"
    with zipfile.ZipFile(zip_path) as zf, zf.open(member) as fh:
        yield from csv.DictReader((line.decode("utf-8-sig") for line in fh))


def build_compact(zip_path, year, team):
    player_names = load_player_names(zip_path, year)
    pa_counts = defaultdict(int)
    pa_start_by_game_side_batter = {}

    for row in iter_play_rows(zip_path, year):
        if row["gametype"] != "regular":
            continue

        key = (row["gid"], row["vis_home"], row["batter"])
        pa_start_by_game_side_batter.setdefault(key, runner_situation(row))

        if row["pa"] != "1":
            continue

        if row["batteam"] != team:
            pa_start_by_game_side_batter.pop(key, None)
            continue

        pa_counts[(row["gid"], row["batter"])] += 1
        start_situation = pa_start_by_game_side_batter.pop(key, runner_situation(row))
        before_final_pitch = runner_situation(row)
        bat_score, fld_score = bat_and_field_scores(row)

        yield {
            "game_date": format_date(row["date"]),
            "game_pk": row["gid"],
            "team": team,
            "player_name": player_names.get(row["batter"], row["batter"]),
            "batter": row["batter"],
            "batter_pa_number_this_game": pa_counts[(row["gid"], row["batter"])],
            "outs_when_up": row["outs_pre"],
            "runner_situation_start": start_situation,
            "runner_situation_before_final_pitch": before_final_pitch,
            "runner_situation_changed_during_pa": 1
            if start_situation == before_final_pitch
            else 0,
            "events": retrosheet_event_name(row),
            "inning": row["inning"],
            "bat_score": bat_score,
            "fld_score": fld_score,
        }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--zip", required=True, type=Path)
    parser.add_argument("--year", required=True, type=int)
    parser.add_argument("--team", default="CLE")
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=OUTPUT_COLUMNS)
        writer.writeheader()
        writer.writerows(build_compact(args.zip, args.year, args.team))


if __name__ == "__main__":
    main()
