"""Rank players with a continuous, innings-aware pressure definition."""

from pressure_rankings import OUTPUT_DIR, batting_rankings, bowling_rankings, load_deliveries


def apply_continuous_pressure(deliveries):
    scored = deliveries.copy()
    scored["late_innings"] = ((scored["legal_balls_before"] - 72) / 48).clip(0, 1)
    scored["wicket_risk"] = (scored["wickets_before"] / 7).clip(0, 1)
    scored["chase_urgency"] = (
        (scored["required_run_rate"] - 7.5) / 6
    ).clip(0, 1).fillna(0)

    # A chase can become tense through the required rate, wickets or time.
    chase_pressure = (
        0.45 * scored["chase_urgency"]
        + 0.30 * scored["wicket_risk"]
        + 0.25 * scored["late_innings"]
    )
    # Setting a target has no required-rate signal, so phase and wickets receive
    # complete weight instead of being capped below the high-pressure threshold.
    first_innings_pressure = (
        0.65 * scored["late_innings"] + 0.35 * scored["wicket_risk"]
    )
    scored["pressure_index"] = chase_pressure.where(
        scored["innings"].eq(2), first_innings_pressure
    )
    scored["pressure_ball"] = scored["pressure_index"].ge(0.60)
    return scored


def main() -> None:
    deliveries = apply_continuous_pressure(load_deliveries())
    batting = batting_rankings(deliveries)
    bowling = bowling_rankings(deliveries)
    batting.to_csv(OUTPUT_DIR / "continuous_batting_rankings.csv", index=False)
    bowling.to_csv(OUTPUT_DIR / "continuous_bowling_rankings.csv", index=False)

    print("Continuous high-pressure deliveries:", int(deliveries["pressure_ball"].sum()))
    print("First-innings high-pressure deliveries:", int(deliveries.loc[deliveries["innings"].eq(1), "pressure_ball"].sum()))
    print("\nTop 15 batters")
    print(batting.head(15)[["striker_name", "pressure_rating", "pressure_balls", "pressure_sr_shrunk", "sr_change"]].round(2).to_string(index=False))
    print("\nTop 15 bowlers")
    print(bowling.head(15)[["bowler_name", "pressure_rating", "pressure_legal_balls", "pressure_economy_shrunk", "economy_change", "pressure_wickets"]].round(2).to_string(index=False))


if __name__ == "__main__":
    main()
