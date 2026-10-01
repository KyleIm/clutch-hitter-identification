#!/usr/bin/env python3
import argparse
from pathlib import Path

import numpy as np
import pandas as pd


RISP_SITUATIONS = {
    "2B",
    "3B",
    "1B+2B",
    "1B+3B",
    "2B+3B",
    "1B+2B+3B",
}

SUCCESS_EVENTS = {
    "single",
    "double",
    "triple",
    "home_run",
}

FAILURE_EVENTS = {
    "field_out",
    "force_out",
    "double_play",
    "grounded_into_double_play",
    "fielders_choice_out",
    "strikeout",
    "strikeout_double_play",
    "sac_fly",
    "field_error",
    "fielders_choice",
}

EXCLUDED_EVENTS = {
    "walk",
    "intent_walk",
    "hit_by_pitch",
    "catcher_interf",
    "sac_bunt",
}


def normalize_runner_situation(value):
    if pd.isna(value):
        return "empty"
    return str(value).replace(" ", "")


def add_risp_flag(df, situation_column):
    df = df.copy()
    df[situation_column] = df[situation_column].map(normalize_runner_situation)
    df["is_risp"] = df[situation_column].isin(RISP_SITUATIONS)
    return df


def add_event_result(df):
    df = df.copy()
    df["event_result"] = "excluded"
    df.loc[df["events"].isin(SUCCESS_EVENTS), "event_result"] = "success"
    df.loc[df["events"].isin(FAILURE_EVENTS), "event_result"] = "failure"

    unknown_events = sorted(
        set(df["events"].dropna()) - SUCCESS_EVENTS - FAILURE_EVENTS - EXCLUDED_EVENTS
    )
    if unknown_events:
        raise ValueError(f"Unknown event values: {unknown_events}")

    return df


def success_rate(success, failure):
    denominator = success + failure
    if denominator == 0:
        return float("nan")
    return success / denominator


def li_ma_s(n_rate, b_rate, alpha):
    if pd.isna(n_rate) or pd.isna(b_rate) or pd.isna(alpha):
        return float("nan")
    if alpha <= 0 or n_rate < 0 or b_rate < 0:
        return float("nan")

    rate_sum = n_rate + b_rate
    if rate_sum == 0:
        return 0.0

    n_term = 0.0
    if n_rate > 0:
        n_term = n_rate * np.log(((1 + alpha) / alpha) * (n_rate / rate_sum))

    b_term = 0.0
    if b_rate > 0:
        b_term = b_rate * np.log((1 + alpha) * (b_rate / rate_sum))

    value = 2 * (n_term + b_term)
    if value < 0 and np.isclose(value, 0):
        value = 0.0
    if value < 0:
        return float("nan")
    sign = 1 if n_rate >= b_rate else -1
    return sign * np.sqrt(value)


def _log_likelihood_term(count, observed_prob, null_prob):
    if count == 0:
        return 0.0
    if observed_prob <= 0 or null_prob <= 0:
        return float("nan")
    return count * np.log(observed_prob / null_prob)


def binomial_on_off_s(on_success, on_failure, off_success, off_failure):
    on_trials = on_success + on_failure
    off_trials = off_success + off_failure
    total_trials = on_trials + off_trials
    total_success = on_success + off_success

    if on_trials == 0 or off_trials == 0:
        return float("nan")

    p_on = on_success / on_trials
    p_off = off_success / off_trials
    p_0 = total_success / total_trials

    on_failure_prob = 1 - p_on
    off_failure_prob = 1 - p_off
    null_failure_prob = 1 - p_0

    terms = [
        _log_likelihood_term(on_success, p_on, p_0),
        _log_likelihood_term(on_failure, on_failure_prob, null_failure_prob),
        _log_likelihood_term(off_success, p_off, p_0),
        _log_likelihood_term(off_failure, off_failure_prob, null_failure_prob),
    ]
    if any(pd.isna(term) for term in terms):
        return float("nan")

    ts_b = 2 * sum(terms)
    if ts_b < 0 and np.isclose(ts_b, 0):
        ts_b = 0.0
    if ts_b < 0:
        return float("nan")

    sign = 1 if p_on >= p_off else -1
    return sign * np.sqrt(ts_b)


def build_player_counts(df):
    rows = []
    for (team, batter, player_name), player_df in df.groupby(
        ["team", "batter", "player_name"], dropna=False
    ):
        risp_df = player_df[player_df["is_risp"]]
        non_risp_df = player_df[~player_df["is_risp"]]

        n_success = int((risp_df["event_result"] == "success").sum())
        n_failure = int((risp_df["event_result"] == "failure").sum())
        n_excluded = int((risp_df["event_result"] == "excluded").sum())
        b_success = int((non_risp_df["event_result"] == "success").sum())
        b_failure = int((non_risp_df["event_result"] == "failure").sum())
        b_excluded = int((non_risp_df["event_result"] == "excluded").sum())
        n = int(len(risp_df))
        b = int(len(non_risp_df))
        n_trials = n_success + n_failure
        b_trials = b_success + b_failure
        alpha = n_trials / b_trials if b_trials else float("nan")
        n_rate = success_rate(n_success, n_failure)
        b_rate = success_rate(b_success, b_failure)

        rows.append(
            {
                "team": team,
                "player_name": player_name,
                "batter": batter,
                "n": n,
                "b": b,
                "n_trials": n_trials,
                "b_trials": b_trials,
                "alpha": alpha,
                "n_success": n_success,
                "n_failure": n_failure,
                "n_excluded": n_excluded,
                "n_rate": n_rate,
                "b_success": b_success,
                "b_failure": b_failure,
                "b_excluded": b_excluded,
                "b_rate": b_rate,
                "S": binomial_on_off_s(
                    n_success,
                    n_failure,
                    b_success,
                    b_failure,
                ),
                "total_pa": int(len(player_df)),
            }
        )

    grouped = pd.DataFrame(rows)

    return grouped[
        [
            "team",
            "player_name",
            "batter",
            "n",
            "b",
            "n_trials",
            "b_trials",
            "alpha",
            "n_success",
            "n_failure",
            "n_excluded",
            "n_rate",
            "b_success",
            "b_failure",
            "b_excluded",
            "b_rate",
            "S",
            "total_pa",
        ]
    ].sort_values(["team", "player_name", "batter"])


def main():
    base_dir = Path(__file__).resolve().parents[1]
    default_input = (
        base_dir
        / "Data"
        / "Retrosheet"
        / "2025"
        / "cle_2025_plate_appearances_compact.csv"
    )

    parser = argparse.ArgumentParser(
        description="Count player PA in RISP (n) and non-RISP (b) situations."
    )
    parser.add_argument("--input", default=default_input, type=Path)
    parser.add_argument(
        "--situation-column",
        default="runner_situation_before_final_pitch",
        choices=["runner_situation_start", "runner_situation_before_final_pitch"],
    )
    parser.add_argument(
        "--output",
        default=base_dir / "Data" / "cle_2025_RISP_sample_counts.csv",
        type=Path,
        help="Optional CSV path for player-level counts.",
    )
    args = parser.parse_args()

    df = pd.read_csv(args.input)
    df = add_risp_flag(df, args.situation_column)
    df = add_event_result(df)
    counts = build_player_counts(df)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    counts.to_csv(args.output, index=False)

    total_n = int(counts["n"].sum())
    total_b = int(counts["b"].sum())
    print(f"input: {args.input}")
    print(f"output: {args.output}")
    print(f"players: {len(counts)}")
    print(f"n_RISP: {total_n}")
    print(f"b_non_RISP: {total_b}")
    print()
    print(
        counts[
            [
                "player_name",
                "n_trials",
                "b_trials",
                "n_rate",
                "b_rate",
                "alpha",
                "S",
            ]
        ].to_string(index=False)
    )


if __name__ == "__main__":
    main()
