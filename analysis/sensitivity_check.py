"""Compare the primary ranking with a stricter pressure definition."""

from pressure_rankings import batting_rankings, bowling_rankings, load_deliveries


def main() -> None:
    deliveries = load_deliveries()
    primary_batters = batting_rankings(deliveries).head(20)["striker_name"]
    primary_bowlers = bowling_rankings(deliveries).head(20)["bowler_name"]

    deliveries["pressure_ball"] = (
        deliveries["legal_balls_before"].ge(102)
        | (
            deliveries["innings"].eq(2)
            & deliveries["balls_remaining"].le(48)
            & deliveries["required_run_rate"].ge(10)
        )
        | (
            deliveries["innings"].eq(2)
            & deliveries["balls_remaining"].le(48)
            & deliveries["wickets_before"].ge(6)
        )
        | (
            deliveries["knock_out"].eq(1)
            & deliveries["legal_balls_before"].ge(90)
        )
    )
    strict_batters = batting_rankings(deliveries).head(20)
    strict_bowlers = bowling_rankings(deliveries).head(20)

    print("Strict-definition batters")
    print(strict_batters[["striker_name", "pressure_rating", "pressure_balls"]].round(2).to_string(index=False))
    print("\nStrict-definition bowlers")
    print(strict_bowlers[["bowler_name", "pressure_rating", "pressure_legal_balls"]].round(2).to_string(index=False))
    print(
        "\nTop-20 overlap",
        "batters",
        len(set(primary_batters) & set(strict_batters["striker_name"])),
        "of 20",
        "| bowlers",
        len(set(primary_bowlers) & set(strict_bowlers["bowler_name"])),
        "of 20",
    )


if __name__ == "__main__":
    main()
