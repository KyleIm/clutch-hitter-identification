# Finding Clutch Hitters

Small baseball data science project exploring whether hitters' outcomes with runners in scoring position (RISP) differ from their non-RISP baseline.

The current analysis builds compact plate-appearance files, labels each PA as RISP or non-RISP, classifies outcomes as success/failure/excluded, and summarizes player-level differences with a signed Li-Ma style `S` statistic.

## Why this exists

RISP performance is often discussed as a repeatable hitter skill. This repo is a first-pass reproducible workflow for separating observed RISP results from a player's broader plate-appearance baseline.

## Repository Layout

```text
.
├── Data/
│   ├── Retrosheet/2025/                 # Compact 2025 team PA extracts
│   ├── *_2025_RISP_sample_counts.csv    # Player-level RISP/non-RISP summaries
│   └── mlb_2025_RISP_S_histogram_PA251.png
├── Script/
│   ├── build_retrosheet_pa_compact.py   # Build compact PA data from Retrosheet event files
│   ├── build_league_RISP_sample_counts.py
│   ├── lima_histogram_RISP_sample.py    # Core RISP labeling and Li-Ma S helpers
│   └── plot_RISP_histogram.py
├── cle_2026_07_plate_appearances_compact.csv
└── cle_2026_07_statcast_pitches_raw.csv
```

## Method

For each hitter:

- `n`: plate appearances with a runner on second and/or third
- `b`: plate appearances without RISP
- `n_rate`: success rate in RISP plate appearances
- `b_rate`: success rate in non-RISP plate appearances
- `S`: signed Li-Ma style statistic comparing `n_rate` with `b_rate`

Success events currently include singles, doubles, triples, and home runs. Walks, hit by pitch, catcher interference, and sacrifice bunts are excluded from the success-rate denominator.

## Reproduce

Create an environment and install dependencies:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Build the 2025 league player summary:

```bash
python Script/build_league_RISP_sample_counts.py
```

Generate the histogram used in `Data/mlb_2025_RISP_S_histogram_PA251.png`:

```bash
python Script/plot_RISP_histogram.py --output Data/mlb_2025_RISP_S_histogram_PA251.png
```

## Current Snapshot

Using 2025 compact PA extracts and a minimum of 251 total PA, the distribution is centered close to zero, which is consistent with the idea that much of observed RISP variation is noisy at one-season sample sizes.

![2025 MLB RISP S Distribution](Data/mlb_2025_RISP_S_histogram_PA251.png)

## Next Steps

- Add year-over-year stability checks for player RISP `S`.
- Compare start-of-PA runner state against final-pitch runner state.
- Add shrinkage estimates for small-sample RISP performance.
- Extend the Cleveland 2026 sample into a team-specific dashboard view.

## Data Notes

The compact 2025 plate-appearance extracts are derived from Retrosheet-style play data. Retrosheet terms and attribution should be followed for any public use of their source data.
