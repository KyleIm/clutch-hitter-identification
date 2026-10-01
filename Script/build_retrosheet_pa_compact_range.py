#!/usr/bin/env python3
import argparse
import csv
from pathlib import Path

from build_retrosheet_pa_compact import OUTPUT_COLUMNS, build_compact, load_player_names


def main():
    base_dir = Path(__file__).resolve().parents[1]
    default_raw_dir = base_dir / "Data" / "Retrosheet" / "Raw"
    default_output_dir = base_dir / "Data" / "Retrosheet" / "Compact"

    parser = argparse.ArgumentParser(
        description="Build compact Retrosheet plate-appearance files by year."
    )
    parser.add_argument("--start-year", default=1998, type=int)
    parser.add_argument("--end-year", default=2025, type=int)
    parser.add_argument("--raw-dir", default=default_raw_dir, type=Path)
    parser.add_argument("--output-dir", default=default_output_dir, type=Path)
    args = parser.parse_args()

    if args.start_year > args.end_year:
        raise ValueError("--start-year must be <= --end-year")

    player_names = load_player_names(args.raw_dir / "allplayers.zip")

    for year in range(args.start_year, args.end_year + 1):
        input_zip = args.raw_dir / "plays" / f"{year}plays.zip"
        output = args.output_dir / f"mlb_{year}_plate_appearances_compact.csv"
        output.parent.mkdir(parents=True, exist_ok=True)

        with output.open("w", newline="") as fh:
            writer = csv.DictWriter(fh, fieldnames=OUTPUT_COLUMNS)
            writer.writeheader()
            rows = 0
            for row in build_compact(input_zip, year, player_names):
                writer.writerow(row)
                rows += 1

        print(f"{year}: wrote {rows} PA rows to {output}")


if __name__ == "__main__":
    main()
