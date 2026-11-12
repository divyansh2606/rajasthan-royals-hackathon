"""Combine the primary and strict pressure scenarios into a robust shortlist."""

from pathlib import Path

import pandas as pd

from pressure_rankings import OUTPUT_DIR, batting_rankings, bowling_rankings, load_deliveries


def strict_pressure(deliveries: pd.DataFrame) -> pd.DataFrame:
    strict = deliveries.copy()
    strict["pressure_ball"] = (
        strict["legal_balls_before"].ge(102)
        | (
            strict["innings"].eq(2)
            & strict["balls_remaining"].le(48)
            & strict["required_run_rate"].ge(10)
        )
        | (
            strict["innings"].eq(2)
            & strict["balls_remaining"].le(48)
            & strict["wickets_before"].ge(6)
        )
        | (strict["knock_out"].eq(1) & strict["legal_balls_before"].ge(90))
    )
    return strict


def combine(
    primary: pd.DataFrame,
    strict: pd.DataFrame,
    id_column: str,
    name_column: str,
) -> pd.DataFrame:
    primary = primary.copy()
    strict = strict.copy()
    primary["primary_rank"] = primary["pressure_rating"].rank(method="min", ascending=False)
    strict["strict_rank"] = strict["pressure_rating"].rank(method="min", ascending=False)
    merged = primary.merge(
        strict[[id_column, "pressure_rating", "strict_rank"]],
        on=id_column,
        how="inner",
        suffixes=("_primary", "_strict"),
    )
    merged["robust_pressure_rating"] = (
        0.60 * merged["pressure_rating_primary"]
        + 0.40 * merged["pressure_rating_strict"]
    )
    merged["robust_rank"] = merged["robust_pressure_rating"].rank(
        method="min", ascending=False
    )
    return merged.sort_values("robust_rank").reset_index(drop=True)


def main() -> None:
    deliveries = load_deliveries()
    primary_batting = batting_rankings(deliveries)
    primary_bowling = bowling_rankings(deliveries)
    strict_deliveries = strict_pressure(deliveries)
    strict_batting = batting_rankings(strict_deliveries)
    strict_bowling = bowling_rankings(strict_deliveries)

    batting = combine(primary_batting, strict_batting, "striker_id", "striker_name")
    bowling = combine(primary_bowling, strict_bowling, "bowler_id", "bowler_name")
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    batting.to_csv(OUTPUT_DIR / "robust_batting_rankings.csv", index=False)
    bowling.to_csv(OUTPUT_DIR / "robust_bowling_rankings.csv", index=False)

    print("Robust top 15 batters")
    print(
        batting.head(15)[
            [
                "robust_rank",
                "striker_name",
                "robust_pressure_rating",
                "primary_rank",
                "strict_rank",
                "pressure_runs",
                "pressure_balls",
            ]
        ].round(2).to_string(index=False)
    )
    print("\nRobust top 15 bowlers")
    print(
        bowling.head(15)[
            [
                "robust_rank",
                "bowler_name",
                "robust_pressure_rating",
                "primary_rank",
                "strict_rank",
                "pressure_runs_conceded",
                "pressure_legal_balls",
                "pressure_wickets",
            ]
        ].round(2).to_string(index=False)
    )


if __name__ == "__main__":
    main()
