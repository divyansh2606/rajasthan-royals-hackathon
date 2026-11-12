"""Create transparent pressure-performance rankings for SupeRR Selector Season 2.

The script uses IPL and T20I matches from the supplied pack. It excludes
abandoned, no-result and revised-overs matches from the primary rankings so
that balls remaining and required run rate mean the same thing everywhere.
"""

from pathlib import Path

import numpy as np
import pandas as pd


DATA_DIR = Path(
    "/Users/divyansh/Downloads/SupeRR Selector Season 2 | Problem Statement | Data Pack/"
    "SupeRR Selector Season 2 | Data Pack"
)
OUTPUT_DIR = Path(__file__).resolve().parent / "output"


def percentile(series: pd.Series, ascending: bool = True) -> pd.Series:
    """Return percentile ranks, with 1 representing the preferred result."""
    return series.rank(pct=True, ascending=ascending)


def load_deliveries() -> pd.DataFrame:
    competitions = pd.read_csv(DATA_DIR / "competitions.csv")
    matches = pd.read_csv(DATA_DIR / "matches.csv")
    deliveries = pd.read_csv(DATA_DIR / "ball_by_ball.csv")

    allowed_competitions = competitions[
        competitions["match_format"].eq("T20I")
        | competitions["comp_name"].str.contains("IPL", case=False, na=False)
    ]
    matches = matches[matches["comp_id"].isin(allowed_competitions["comp_id"])]
    matches = matches[
        ~matches["result"].str.contains("No Result|Abandoned", case=False, na=False)
    ]
    matches = matches[
        matches["first_inn_revised_overs"].isna()
        & matches["second_inn_revised_overs"].isna()
        & matches["revised_target"].isna()
    ].copy()

    deliveries = deliveries[deliveries["match_id"].isin(matches["match_id"])].copy()
    deliveries = deliveries[deliveries["innings"].isin([1, 2])].copy()
    deliveries = deliveries.merge(
        matches[["match_id", "knock_out", "match_date"]], on="match_id", how="left"
    )
    deliveries = deliveries.sort_values(
        ["match_id", "innings", "innings_ball_num"]
    ).reset_index(drop=True)

    deliveries["is_wide"] = deliveries["extras_type"].eq("wide")
    deliveries["is_no_ball"] = deliveries["extras_type"].eq("Overstep")
    deliveries["is_legal"] = ~(deliveries["is_wide"] | deliveries["is_no_ball"])
    deliveries["team_runs"] = (
        deliveries["runs"]
        + deliveries["extras_2_runs"]
        + deliveries["extras_type"].notna().astype(int)
    )
    deliveries["bowler_runs"] = (
        deliveries["runs"]
        + deliveries["extras_2_runs"]
        + (deliveries["is_wide"] | deliveries["is_no_ball"]).astype(int)
    )

    innings_key = ["match_id", "innings"]
    deliveries["runs_before"] = (
        deliveries.groupby(innings_key)["team_runs"].cumsum() - deliveries["team_runs"]
    )
    deliveries["legal_balls_before"] = (
        deliveries.groupby(innings_key)["is_legal"].cumsum() - deliveries["is_legal"]
    )
    deliveries["wickets_before"] = (
        deliveries.groupby(innings_key)["is_wicket"].cumsum() - deliveries["is_wicket"]
    )

    first_innings_total = (
        deliveries[deliveries["innings"].eq(1)]
        .groupby("match_id")["team_runs"]
        .sum()
        .add(1)
        .rename("target")
    )
    deliveries = deliveries.merge(first_innings_total, on="match_id", how="left")
    deliveries["balls_remaining"] = 120 - deliveries["legal_balls_before"]
    deliveries["runs_required"] = deliveries["target"] - deliveries["runs_before"]
    deliveries["required_run_rate"] = np.where(
        deliveries["innings"].eq(2) & deliveries["balls_remaining"].gt(0),
        deliveries["runs_required"] * 6 / deliveries["balls_remaining"],
        np.nan,
    )

    deliveries["pressure_ball"] = (
        deliveries["legal_balls_before"].ge(90)
        | (
            deliveries["innings"].eq(2)
            & deliveries["balls_remaining"].le(60)
            & deliveries["required_run_rate"].ge(9)
        )
        | (
            deliveries["innings"].eq(2)
            & deliveries["balls_remaining"].le(60)
            & deliveries["wickets_before"].ge(5)
        )
        | (
            deliveries["knock_out"].eq(1)
            & deliveries["legal_balls_before"].ge(72)
        )
    )
    return deliveries


def batting_rankings(deliveries: pd.DataFrame) -> pd.DataFrame:
    bat = deliveries[deliveries["is_legal"]].copy()
    bat["pressure_runs"] = np.where(bat["pressure_ball"], bat["runs"], 0)
    bat["pressure_balls"] = bat["pressure_ball"].astype(int)
    bat["pressure_dismissals"] = np.where(
        bat["pressure_ball"] & bat["dismissed_player_id"].eq(bat["striker_id"]), 1, 0
    )
    bat["normal_runs"] = np.where(~bat["pressure_ball"], bat["runs"], 0)
    bat["normal_balls"] = (~bat["pressure_ball"]).astype(int)

    grouped = bat.groupby(["striker_id", "striker_name"], as_index=False).agg(
        pressure_runs=("pressure_runs", "sum"),
        pressure_balls=("pressure_balls", "sum"),
        pressure_dismissals=("pressure_dismissals", "sum"),
        normal_runs=("normal_runs", "sum"),
        normal_balls=("normal_balls", "sum"),
    )
    global_pressure_rate = bat.loc[bat["pressure_ball"], "runs"].mean()
    grouped["pressure_sr_shrunk"] = 100 * (
        grouped["pressure_runs"] + 36 * global_pressure_rate
    ) / (grouped["pressure_balls"] + 36)
    grouped["normal_sr"] = 100 * grouped["normal_runs"] / grouped["normal_balls"]
    grouped["sr_change"] = grouped["pressure_sr_shrunk"] - grouped["normal_sr"]

    pressure_innings = bat[bat["pressure_ball"]].groupby(
        ["striker_id", "striker_name", "match_id"], as_index=False
    ).agg(
        pressure_match_runs=("runs", "sum"),
        pressure_match_balls=("is_legal", "sum"),
    )
    pressure_innings = pressure_innings.merge(
        grouped[["striker_id", "normal_sr"]], on="striker_id", how="left"
    )
    pressure_innings["at_or_above_baseline"] = (
        pressure_innings["pressure_match_balls"].ge(6)
        & (
            100
            * pressure_innings["pressure_match_runs"]
            / pressure_innings["pressure_match_balls"]
        ).ge(pressure_innings["normal_sr"])
    )
    consistency = pressure_innings[pressure_innings["pressure_match_balls"].ge(6)].groupby(
        "striker_id", as_index=False
    ).agg(
        pressure_innings=("match_id", "nunique"),
        pressure_innings_at_or_above_baseline=("at_or_above_baseline", "mean"),
    )
    grouped = grouped.merge(consistency, on="striker_id", how="left")
    eligible = grouped[
        grouped["pressure_balls"].ge(30)
        & grouped["normal_balls"].ge(120)
        & grouped["pressure_innings"].ge(3)
    ].copy()
    eligible["pressure_reliability"] = eligible["pressure_balls"] / (
        eligible["pressure_balls"] + 36
    )
    eligible["pressure_rating"] = 100 * (
        0.45 * percentile(eligible["pressure_sr_shrunk"])
        + 0.25 * percentile(eligible["sr_change"])
        + 0.15 * percentile(eligible["pressure_innings_at_or_above_baseline"])
        + 0.15 * percentile(eligible["pressure_reliability"])
    )
    return eligible.sort_values("pressure_rating", ascending=False).reset_index(drop=True)


def bowling_rankings(deliveries: pd.DataFrame) -> pd.DataFrame:
    bowl = deliveries.copy()
    credited_wicket = bowl["is_wicket"] & ~bowl["dismissal_type"].str.lower().eq("run out")
    bowl["pressure_runs_conceded"] = np.where(
        bowl["pressure_ball"], bowl["bowler_runs"], 0
    )
    bowl["pressure_legal_balls"] = (bowl["pressure_ball"] & bowl["is_legal"]).astype(int)
    bowl["pressure_wickets"] = np.where(bowl["pressure_ball"] & credited_wicket, 1, 0)
    bowl["normal_runs_conceded"] = np.where(~bowl["pressure_ball"], bowl["bowler_runs"], 0)
    bowl["normal_legal_balls"] = (~bowl["pressure_ball"] & bowl["is_legal"]).astype(int)

    grouped = bowl.groupby(["bowler_id", "bowler_name"], as_index=False).agg(
        pressure_runs_conceded=("pressure_runs_conceded", "sum"),
        pressure_legal_balls=("pressure_legal_balls", "sum"),
        pressure_wickets=("pressure_wickets", "sum"),
        normal_runs_conceded=("normal_runs_conceded", "sum"),
        normal_legal_balls=("normal_legal_balls", "sum"),
    )
    global_pressure_rate = (
        bowl.loc[bowl["pressure_ball"], "bowler_runs"].sum()
        / bowl.loc[bowl["pressure_ball"] & bowl["is_legal"], "is_legal"].sum()
    )
    grouped["pressure_economy_shrunk"] = 6 * (
        grouped["pressure_runs_conceded"] + 36 * global_pressure_rate
    ) / (grouped["pressure_legal_balls"] + 36)
    grouped["normal_economy"] = 6 * grouped["normal_runs_conceded"] / grouped["normal_legal_balls"]
    grouped["economy_change"] = grouped["normal_economy"] - grouped["pressure_economy_shrunk"]
    grouped["pressure_wicket_rate"] = 24 * grouped["pressure_wickets"] / grouped["pressure_legal_balls"]

    pressure_spells = bowl[bowl["pressure_ball"]].groupby(
        ["bowler_id", "bowler_name", "match_id"], as_index=False
    ).agg(
        pressure_match_runs=("bowler_runs", "sum"),
        pressure_match_balls=("is_legal", "sum"),
    )
    pressure_spells = pressure_spells.merge(
        grouped[["bowler_id", "normal_economy"]], on="bowler_id", how="left"
    )
    pressure_spells["at_or_below_baseline"] = (
        pressure_spells["pressure_match_balls"].ge(6)
        & (
            6
            * pressure_spells["pressure_match_runs"]
            / pressure_spells["pressure_match_balls"]
        ).le(pressure_spells["normal_economy"])
    )
    consistency = pressure_spells[pressure_spells["pressure_match_balls"].ge(6)].groupby(
        "bowler_id", as_index=False
    ).agg(
        pressure_spells=("match_id", "nunique"),
        pressure_spells_at_or_below_baseline=("at_or_below_baseline", "mean"),
    )
    grouped = grouped.merge(consistency, on="bowler_id", how="left")
    eligible = grouped[
        grouped["pressure_legal_balls"].ge(24)
        & grouped["normal_legal_balls"].ge(120)
        & grouped["pressure_spells"].ge(3)
    ].copy()
    eligible["pressure_reliability"] = eligible["pressure_legal_balls"] / (
        eligible["pressure_legal_balls"] + 36
    )
    eligible["pressure_rating"] = 100 * (
        0.45 * percentile(eligible["pressure_economy_shrunk"], ascending=False)
        + 0.20 * percentile(eligible["economy_change"])
        + 0.15 * percentile(eligible["pressure_wicket_rate"])
        + 0.10 * percentile(eligible["pressure_spells_at_or_below_baseline"])
        + 0.10 * percentile(eligible["pressure_reliability"])
    )
    return eligible.sort_values("pressure_rating", ascending=False).reset_index(drop=True)


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    deliveries = load_deliveries()
    batting = batting_rankings(deliveries)
    bowling = bowling_rankings(deliveries)
    batting.to_csv(OUTPUT_DIR / "batting_pressure_rankings.csv", index=False)
    bowling.to_csv(OUTPUT_DIR / "bowling_pressure_rankings.csv", index=False)

    print("Standard IPL and T20I deliveries analysed:", len(deliveries))
    print("Pressure deliveries:", int(deliveries["pressure_ball"].sum()))
    print("\nTop 20 batters")
    print(
        batting.head(20)[
            [
                "striker_name",
                "pressure_rating",
                "pressure_runs",
                "pressure_balls",
                "pressure_sr_shrunk",
                "normal_sr",
                "sr_change",
            ]
        ].round(2).to_string(index=False)
    )
    print("\nTop 20 bowlers")
    print(
        bowling.head(20)[
            [
                "bowler_name",
                "pressure_rating",
                "pressure_runs_conceded",
                "pressure_legal_balls",
                "pressure_economy_shrunk",
                "normal_economy",
                "economy_change",
                "pressure_wickets",
            ]
        ].round(2).to_string(index=False)
    )


if __name__ == "__main__":
    main()
