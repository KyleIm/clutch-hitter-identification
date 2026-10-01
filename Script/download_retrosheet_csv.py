#!/usr/bin/env python3
import argparse
from pathlib import Path
from urllib.request import Request, urlopen


BASE_URL = "https://www.retrosheet.org/downloads"
USER_AGENT = "clutch-hitter-identification/0.1"
CHUNK_SIZE = 1024 * 1024


def download(url, output_path):
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if output_path.exists() and output_path.stat().st_size > 0:
        print(f"skip existing: {output_path}")
        return

    request = Request(url, headers={"User-Agent": USER_AGENT})
    with urlopen(request, timeout=120) as response, output_path.open("wb") as out:
        total_header = response.headers.get("Content-Length")
        total = int(total_header) if total_header else None
        downloaded = 0
        while True:
            chunk = response.read(CHUNK_SIZE)
            if not chunk:
                break
            out.write(chunk)
            downloaded += len(chunk)
            if total:
                pct = 100 * downloaded / total
                print(
                    f"\r{output_path.name}: {pct:5.1f}% "
                    f"({downloaded / 1024 / 1024:.1f}/{total / 1024 / 1024:.1f} MB)",
                    end="",
                    flush=True,
                )
        print()


def main():
    base_dir = Path(__file__).resolve().parents[1]
    default_output_dir = base_dir / "Data" / "Retrosheet" / "Raw"

    parser = argparse.ArgumentParser(
        description="Download Retrosheet parsed play-by-play CSV zip files."
    )
    parser.add_argument("--start-year", default=1998, type=int)
    parser.add_argument("--end-year", default=2025, type=int)
    parser.add_argument("--output-dir", default=default_output_dir, type=Path)
    args = parser.parse_args()

    if args.start_year > args.end_year:
        raise ValueError("--start-year must be <= --end-year")

    download(
        f"{BASE_URL}/allplayers.zip",
        args.output_dir / "allplayers.zip",
    )

    for year in range(args.start_year, args.end_year + 1):
        download(
            f"{BASE_URL}/plays/{year}plays.zip",
            args.output_dir / "plays" / f"{year}plays.zip",
        )


if __name__ == "__main__":
    main()
