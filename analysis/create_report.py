"""Build the Round 1 pressure reliability report from the ranking outputs."""

from pathlib import Path

import pandas as pd
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "output" / "pdf" / "RR_Pressure_Reliability_Report.pdf"
DATA = ROOT / "analysis" / "output"
NAVY = colors.HexColor("#101E53")
PINK = colors.HexColor("#E31C79")
INK = colors.HexColor("#1D2542")
MUTED = colors.HexColor("#64708B")
PALE = colors.HexColor("#F7F6FB")
PALE_PINK = colors.HexColor("#FFF0F6")
LINE = colors.HexColor("#E1E3EC")


def fmt(value, digits=1):
    return f"{value:.{digits}f}"


def p(text, style):
    return Paragraph(text, style)


def footer(canvas, doc):
    canvas.saveState()
    canvas.setStrokeColor(PINK)
    canvas.setLineWidth(1.2)
    canvas.line(40, 34, A4[0] - 40, 34)
    canvas.setFillColor(MUTED)
    canvas.setFont("Helvetica", 7.5)
    canvas.drawString(40, 21, "SUPE RR SELECTOR S2  |  ROUND 1  |  RR PRESSURE SHORTLIST")
    canvas.drawRightString(A4[0] - 40, 21, f"{doc.page:02d}")
    canvas.restoreState()


def styled_table(data, widths, header=True, font_size=8, padding=6, background=None):
    table = Table(data, colWidths=widths, repeatRows=1 if header else 0, hAlign="LEFT")
    commands = [
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("GRID", (0, 0), (-1, -1), 0.35, LINE),
        ("LEFTPADDING", (0, 0), (-1, -1), padding),
        ("RIGHTPADDING", (0, 0), (-1, -1), padding),
        ("TOPPADDING", (0, 0), (-1, -1), padding),
        ("BOTTOMPADDING", (0, 0), (-1, -1), padding),
    ]
    if header:
        commands += [
            ("BACKGROUND", (0, 0), (-1, 0), NAVY),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, PALE]),
        ]
    elif background:
        commands.append(("BACKGROUND", (0, 0), (-1, -1), background))
    table.setStyle(TableStyle(commands))
    return table


def ranking_table(frame, role, styles):
    if role == "bat":
        headers = ["#", "Player", "Score", "Pressure SR", "SR uplift", "Balls", "Innings"]
        rows = [[
            str(int(row.robust_rank)), row.striker_name,
            fmt(row.robust_pressure_rating, 2), fmt(row.pressure_sr_shrunk),
            f"+{fmt(row.sr_change)}", str(int(row.pressure_balls)),
            str(int(row.pressure_innings)),
        ] for row in frame.head(10).itertuples()]
        title = "Batters"
    else:
        headers = ["#", "Player", "Score", "Pressure econ", "Econ gain", "Balls", "Wkts"]
        rows = [[
            str(int(row.robust_rank)), row.bowler_name,
            fmt(row.robust_pressure_rating, 2), fmt(row.pressure_economy_shrunk, 2),
            f"{row.economy_change:+.2f}", str(int(row.pressure_legal_balls)),
            str(int(row.pressure_wickets)),
        ] for row in frame.head(10).itertuples()]
        title = "Bowlers"
    data = [[p(cell, styles["tablehead"]) for cell in headers]]
    data += [[p(str(cell), styles["tablecell"]) for cell in row] for row in rows]
    widths = [0.40*inch, 2.20*inch, 0.75*inch, 1.10*inch, 1.05*inch, 0.85*inch, 0.75*inch]
    return [p(title, styles["h2"]), styled_table(data, widths, padding=4)]


def main():
    bat = pd.read_csv(DATA / "robust_batting_rankings.csv")
    raw_bowl = pd.read_csv(DATA / "robust_bowling_rankings.csv")

    # These two Pakistan internationals rank highly in the data, but they are
    # removed before making IPL 2027 auction recommendations.
    ineligible_for_ipl = {"Mohammad Nawaz", "Abrar Ahmed"}
    excluded = raw_bowl.loc[raw_bowl["bowler_name"].isin(ineligible_for_ipl)].copy()
    bowl = raw_bowl.loc[~raw_bowl["bowler_name"].isin(ineligible_for_ipl)].copy()
    bowl["robust_rank"] = range(1, len(bowl) + 1)
    bowl.to_csv(DATA / "auction_ready_bowling_rankings.csv", index=False)
    OUT.parent.mkdir(parents=True, exist_ok=True)

    doc = SimpleDocTemplate(
        str(OUT), pagesize=A4, leftMargin=40, rightMargin=40,
        topMargin=40, bottomMargin=48,
        title="Pressure Reliability Report | Rajasthan Royals",
        author="SupeRR Selector Season 2 | Round 1",
        subject="IPL 2027 auction shortlist methodology",
    )
    base = getSampleStyleSheet()
    styles = {
        "kicker": ParagraphStyle("kicker", parent=base["Normal"], fontName="Helvetica-Bold", fontSize=8, leading=10, textColor=PINK, spaceAfter=8, tracking=1.1),
        "cover": ParagraphStyle("cover", parent=base["Title"], fontName="Helvetica-Bold", fontSize=30, leading=34, textColor=colors.white, alignment=TA_LEFT, spaceAfter=7),
        "coverdeck": ParagraphStyle("coverdeck", parent=base["Normal"], fontSize=11, leading=16, textColor=colors.HexColor("#E5E8F7"), spaceAfter=5),
        "h1": ParagraphStyle("h1", parent=base["Heading1"], fontName="Helvetica-Bold", fontSize=21, leading=25, textColor=INK, spaceBefore=2, spaceAfter=8),
        "h2": ParagraphStyle("h2", parent=base["Heading2"], fontName="Helvetica-Bold", fontSize=13, leading=16, textColor=INK, spaceBefore=9, spaceAfter=6),
        "body": ParagraphStyle("body", parent=base["BodyText"], fontName="Helvetica", fontSize=9.1, leading=13.2, textColor=INK, spaceAfter=7),
        "small": ParagraphStyle("small", parent=base["BodyText"], fontName="Helvetica", fontSize=7.8, leading=10.4, textColor=MUTED, spaceAfter=5),
        "metric": ParagraphStyle("metric", parent=base["Normal"], fontName="Helvetica-Bold", fontSize=20, leading=22, textColor=NAVY, alignment=TA_CENTER),
        "metriclabel": ParagraphStyle("metriclabel", parent=base["Normal"], fontSize=7.5, leading=10, textColor=MUTED, alignment=TA_CENTER),
        "tablehead": ParagraphStyle("tablehead", parent=base["Normal"], fontName="Helvetica-Bold", fontSize=6.8, leading=8.2, textColor=colors.white, alignment=TA_CENTER),
        "tablecell": ParagraphStyle("tablecell", parent=base["Normal"], fontName="Helvetica", fontSize=7.3, leading=8.6, textColor=INK),
        "tablecellcenter": ParagraphStyle("tablecellcenter", parent=base["Normal"], fontName="Helvetica", fontSize=7.3, leading=8.6, textColor=INK, alignment=TA_CENTER),
        "callout": ParagraphStyle("callout", parent=base["BodyText"], fontName="Helvetica", fontSize=9, leading=13, textColor=INK, spaceAfter=0),
    }

    story = []

    # Page 1: the decision in one glance.
    hero = Table([
        [p("SUPE RR SELECTOR SEASON 2  /  ROUND 1", styles["coverdeck"])],
        [p("Pressure Reliability Report", styles["cover"])],
        [p("How we built the shortlist for Rajasthan Royals' IPL 2027 auction", styles["coverdeck"])],
    ], colWidths=[7.1*inch])
    hero.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), NAVY),
        ("BOX", (0, 0), (-1, -1), 0, NAVY),
        ("LEFTPADDING", (0, 0), (-1, -1), 19),
        ("RIGHTPADDING", (0, 0), (-1, -1), 19),
        ("TOPPADDING", (0, 0), (-1, 0), 18),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 4),
        ("TOPPADDING", (0, 1), (-1, 1), 4),
        ("BOTTOMPADDING", (0, 1), (-1, 1), 4),
        ("TOPPADDING", (0, 2), (-1, 2), 4),
        ("BOTTOMPADDING", (0, 2), (-1, 2), 18),
    ]))
    story += [hero, Spacer(1, 14)]

    metrics = [[
        p("789", styles["metric"]),
        p("188,330", styles["metric"]),
        p("58,485", styles["metric"]),
    ], [
        p("matches after scope filters", styles["metriclabel"]),
        p("innings 1 and 2 deliveries", styles["metriclabel"]),
        p("deliveries flagged as pressure", styles["metriclabel"]),
    ]]
    metric_table = Table(metrics, colWidths=[7.1*inch/3]*3)
    metric_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), PALE),
        ("BOX", (0, 0), (-1, -1), 0.5, LINE),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, LINE),
        ("TOPPADDING", (0, 0), (-1, 0), 12),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 3),
        ("TOPPADDING", (0, 1), (-1, 1), 0),
        ("BOTTOMPADDING", (0, 1), (-1, 1), 11),
    ]))
    story += [metric_table, Spacer(1, 11), p("The call", styles["h2"])]
    story += [p(
        "We ranked players by what they did when the innings got difficult, then checked whether the order held under a tougher definition of pressure. For the final auction list, we kept the top performers who can realistically be considered for the IPL. That last eligibility check matters: a player can score well in the data and still be the wrong name to put forward for this auction.",
        styles["body"],
    )]
    leader_rows = [[
        p("TOP BATTER", styles["small"]), p("TOP IPL-ELIGIBLE BOWLER", styles["small"])
    ], [
        p("Tristan Stubbs", styles["h2"]), p("Akeal Hosein", styles["h2"])
    ], [
        p("90.13 robust score  |  181.06 pressure SR", styles["small"]),
        p("89.31 robust score  |  7.81 pressure economy", styles["small"])
    ]]
    leaders = Table(leader_rows, colWidths=[3.55*inch, 3.55*inch])
    leaders.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), PALE_PINK),
        ("BOX", (0, 0), (-1, -1), 0.6, colors.HexColor("#F3C6D9")),
        ("INNERGRID", (0, 0), (-1, -1), 0.6, colors.HexColor("#F3C6D9")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 12),
        ("RIGHTPADDING", (0, 0), (-1, -1), 12),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    story += [leaders, Spacer(1, 8), p(
        "This report is meant to make the choices easy to follow. The score is a ranking aid, not a prediction of next season's performance or a bid price.",
        styles["small"],
    ), PageBreak()]

    # Page 2: source pack, scope, and delivery preparation.
    story += [p("01  |  Data and scope", styles["kicker"]), p("Start with a clean comparison", styles["h1"])]
    story += [p(
        "We used the Rajasthan Royals data pack's competitions, matches and ball-by-ball files. The pack covers 22 January 2022 to 1 November 2026. We kept IPL and T20I matches so the performance sample included both franchise and international T20 pressure, while the final auction list was filtered separately for IPL eligibility.",
        styles["body"],
    )]
    scope_data = [
        [p("Step", styles["tablehead"]), p("What we kept or removed", styles["tablehead"]), p("Why it matters", styles["tablehead"])],
        [p("Competition", styles["tablecell"]), p("IPL and T20I matches in the supplied pack", styles["tablecell"]), p("Keeps the analysis within short-format cricket and the brief's main competitions.", styles["tablecell"])],
        [p("Match result", styles["tablecell"]), p("Completed matches only; abandoned and no-result games removed", styles["tablecell"]), p("An incomplete game can leave a misleading innings state or target.", styles["tablecell"])],
        [p("Revised conditions", styles["tablecell"]), p("Removed games with revised overs or a revised target", styles["tablecell"]), p("The pressure rules assume a standard 20-over innings and a standard chase target.", styles["tablecell"])],
        [p("Innings", styles["tablecell"]), p("Both first and second innings; only innings 1 and 2", styles["tablecell"]), p("Late-innings pressure matters when setting a target too, not only when chasing.", styles["tablecell"])],
    ]
    story += [styled_table(scope_data, [1.05*inch, 2.75*inch, 3.3*inch], padding=7), Spacer(1, 11)]
    story += [p("How we treated a delivery", styles["h2"])]
    story += [p(
        "A legal ball is a delivery that is not a wide or no-ball. Batter strike rate uses legal balls only. Bowler runs conceded include the run and penalty for wides and no-balls, but do not charge byes or leg byes to the bowler. Wickets credited to a bowler exclude run-outs. We sorted balls in match order and calculated balls remaining, wickets already lost and the chase's required rate before tagging pressure.",
        styles["body"],
    )]
    note = Table([[p(
        "<b>Sample after these checks:</b> 789 matches, 188,330 deliveries across both innings. Of these, 58,485 met the primary pressure definition. The window in the pack ends on 1 November 2026; this is a historical sample, not a complete record of every T20 league.",
        styles["callout"],
    )]], colWidths=[7.1*inch])
    note.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), PALE),
        ("BOX", (0, 0), (-1, -1), 0.6, LINE),
        ("LEFTPADDING", (0, 0), (-1, -1), 11),
        ("RIGHTPADDING", (0, 0), (-1, -1), 11),
        ("TOPPADDING", (0, 0), (-1, -1), 9),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 9),
    ]))
    story += [note, PageBreak()]

    # Page 3: operational pressure definitions.
    story += [p("02  |  Pressure definition", styles["kicker"]), p("Pressure is a match state", styles["h1"])]
    story += [p(
        "We did not label a player as a pressure performer because of reputation. We flagged a delivery when the game state met one or more explicit conditions. The primary rule was designed to capture late overs, urgent chases, wicket pressure and knockout moments.",
        styles["body"],
    )]
    conditions = [
        [p("Signal", styles["tablehead"]), p("Primary scenario", styles["tablehead"]), p("Stricter check", styles["tablehead"]), p("Game situation", styles["tablehead"])],
        [p("Late phase", styles["tablecell"]), p("90+ legal balls completed", styles["tablecell"]), p("102+ legal balls completed", styles["tablecell"]), p("Final five overs versus final three overs", styles["tablecell"])],
        [p("Chase urgency", styles["tablecell"]), p("60 or fewer balls left and required rate 9+", styles["tablecell"]), p("48 or fewer balls left and required rate 10+", styles["tablecell"]), p("A chase with little time and a high ask", styles["tablecell"])],
        [p("Wickets down", styles["tablecell"]), p("60 or fewer balls left and 5+ wickets lost", styles["tablecell"]), p("48 or fewer balls left and 6+ wickets lost", styles["tablecell"]), p("A late chase with limited wickets in hand", styles["tablecell"])],
        [p("Knockout phase", styles["tablecell"]), p("Knockout match after 72 legal balls", styles["tablecell"]), p("Knockout match after 90 legal balls", styles["tablecell"]), p("Late innings in a high-stakes match", styles["tablecell"])],
    ]
    story += [styled_table(conditions, [1.0*inch, 1.95*inch, 1.95*inch, 2.2*inch], padding=7), Spacer(1, 12)]
    story += [p("Why there are two definitions", styles["h2"])]
    story += [p(
        "One cutoff can move a ranking. We used the primary scenario for the main read, then built a tougher version that starts later and asks more of a chase or a battering team. The final score is 60% primary rating and 40% strict rating. A player who stays near the top under both definitions is a safer shortlist choice than one who only rises under the more generous rule.",
        styles["body"],
    )]
    story += [p(
        "The primary rule flags 58,485 deliveries; the stricter rule flags 37,819. The primary sample includes 25,058 first-innings and 33,427 second-innings pressure deliveries. That split is intentional: a team defending a total still has pressure overs to bowl and a target to set.",
        styles["body"],
    )]
    story += [p("A separate check", styles["h2"]), p(
        "We also tried a continuous pressure index using late-innings phase, wickets lost and chase urgency. It was useful as a diagnostic, especially for first-innings pressure, but it changed some short-sample batter positions more sharply. We kept the rule-based score as the final ranking because its triggers are easier to explain and reproduce.",
        styles["body"],
    ), PageBreak()]

    # Page 4: score construction.
    story += [p("03  |  Scoring", styles["kicker"]), p("Reward output, consistency and evidence", styles["h1"])]
    story += [p(
        "We ranked batters and bowlers separately. Each component is converted to a percentile among players who pass the minimum sample rules, then combined into a 0-100 rating. A lower bowling economy is better; a higher value on the other positive components is better.",
        styles["body"],
    )]
    approach = Table([
        [p("TOOLS", styles["tablehead"]), p("METHOD", styles["tablehead"]), p("WHY NO ML MODEL?", styles["tablehead"])],
        [
            p("Python, pandas and NumPy. We used them to read the supplied CSVs, filter matches, calculate match-state fields, aggregate player records and export the ranked tables.", styles["tablecell"]),
            p("Descriptive data analysis, feature engineering and a rule-based percentile score. We also ran a stricter pressure scenario and a continuous-pressure diagnostic.", styles["tablecell"]),
            p("The pack has past ball-by-ball results, but no labelled future outcome such as next-season impact or auction value. We did not train an ML model; instead, we chose a score that can be checked back to the deliveries.", styles["tablecell"]),
        ],
    ], colWidths=[2.36*inch, 2.36*inch, 2.36*inch])
    approach.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), NAVY),
        ("BACKGROUND", (0, 1), (-1, 1), PALE),
        ("GRID", (0, 0), (-1, -1), 0.45, LINE),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 7),
        ("RIGHTPADDING", (0, 0), (-1, -1), 7),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
    ]))
    story += [approach, Spacer(1, 8)]
    scoring = [
        [p("Role", styles["tablehead"]), p("Component", styles["tablehead"]), p("Weight", styles["tablehead"]), p("What it rewards", styles["tablehead"])],
        [p("Batter", styles["tablecell"]), p("Shrunk pressure strike rate", styles["tablecell"]), p("45%", styles["tablecellcenter"]), p("Run scoring while pressure is on", styles["tablecell"])],
        [p("Batter", styles["tablecell"]), p("Pressure SR uplift", styles["tablecell"]), p("25%", styles["tablecellcenter"]), p("Performance above the player's normal SR", styles["tablecell"])],
        [p("Batter", styles["tablecell"]), p("Innings at or above baseline", styles["tablecell"]), p("15%", styles["tablecellcenter"]), p("Repeatability across pressure innings", styles["tablecell"])],
        [p("Batter", styles["tablecell"]), p("Sample reliability", styles["tablecell"]), p("15%", styles["tablecellcenter"]), p("More pressure balls provide stronger evidence", styles["tablecell"])],
        [p("Bowler", styles["tablecell"]), p("Shrunk pressure economy", styles["tablecell"]), p("45%", styles["tablecellcenter"]), p("Run control when pressure is on", styles["tablecell"])],
        [p("Bowler", styles["tablecell"]), p("Economy improvement", styles["tablecell"]), p("20%", styles["tablecellcenter"]), p("Pressure economy relative to normal economy", styles["tablecell"])],
        [p("Bowler", styles["tablecell"]), p("Pressure wicket rate", styles["tablecell"]), p("15%", styles["tablecellcenter"]), p("Taking credited wickets in pressure overs", styles["tablecell"])],
        [p("Bowler", styles["tablecell"]), p("Spells at or below baseline", styles["tablecell"]), p("10%", styles["tablecellcenter"]), p("Repeatability across pressure spells", styles["tablecell"])],
        [p("Bowler", styles["tablecell"]), p("Sample reliability", styles["tablecell"]), p("10%", styles["tablecellcenter"]), p("More pressure balls provide stronger evidence", styles["tablecell"])],
    ]
    story += [styled_table(scoring, [0.72*inch, 1.75*inch, 0.62*inch, 4.01*inch], padding=5), Spacer(1, 9)]
    thresholds = [
        [p("Batter minimum", styles["tablehead"]), p("Bowler minimum", styles["tablehead"])],
        [p("30 pressure balls, 120 normal balls and 3 pressure innings", styles["tablecell"]), p("24 pressure legal balls, 120 normal legal balls and 3 pressure spells", styles["tablecell"])],
    ]
    story += [styled_table(thresholds, [3.55*inch, 3.55*inch], padding=7), Spacer(1, 9)]
    story += [p("Why shrink the pressure rate?", styles["h2"]), p(
        "A rate from a small sample can look extreme by chance. For both roles, we blend each player's pressure rate with the overall pressure rate as if the player had 36 extra balls of average performance. As the player's own pressure sample grows, those 36 balls matter less. This keeps a short burst from outranking a much stronger, longer record by itself.",
        styles["body"],
    )]
    story += [p(
        "The minimums are eligibility checks, not guarantees of certainty. Matthew Humphreys clears the bowling thresholds with 85 pressure legal balls, but his evidence base is still smaller than a bowler such as Jasprit Bumrah with 668 pressure legal balls. We show the volume beside the rating so that difference remains visible.",
        styles["body"],
    )]
    pipeline_cells = [
        [p("01  FILTER", styles["tablehead"]), p("02  SHRINK", styles["tablehead"]), p("03  RANK", styles["tablehead"]), p("04  STRESS-TEST", styles["tablehead"]), p("05  CHECK POOL", styles["tablehead"])],
        [p("Set minimum samples", styles["tablecellcenter"]), p("Stabilize small pressure samples", styles["tablecellcenter"]), p("Combine weighted percentiles", styles["tablecellcenter"]), p("Blend primary and strict scores", styles["tablecellcenter"]), p("Remove IPL-ineligible names", styles["tablecellcenter"])],
    ]
    story += [Spacer(1, 5), styled_table(pipeline_cells, [1.42*inch]*5, padding=6), PageBreak()]

    # Page 5: rankings and rationale.
    story += [p("04  |  Shortlist", styles["kicker"]), p("The final ten in each role", styles["h1"])]
    story += [p(
        "The lists below follow the robust score order. Batter SR uplift is pressure strike rate minus normal strike rate; a positive number means the batter scored faster under pressure. Bowler econ gain is normal economy minus pressure economy; a positive number means the bowler conceded fewer runs per over under pressure.",
        styles["small"],
    )]
    story += ranking_table(bat, "bat", styles)
    story += [Spacer(1, 8)]
    story += ranking_table(bowl, "bowl", styles)
    story += [Spacer(1, 8), p(
        "We applied auction eligibility after calculating the performance scores. Mohammad Nawaz (raw robust rank 1, score 90.29) and Abrar Ahmed (raw robust rank 4, score 87.49) are Pakistan internationals. We leave them out of an IPL 2027 auction recommendation and move the next eligible bowlers up. Their presence in a submission dropdown does not change that decision.",
        styles["small"],
    ), PageBreak()]

    # Page 6: notes on the names and how to read the list.
    story += [p("05  |  Reading the results", styles["kicker"]), p("What the scores say - and what they don't", styles["h1"])]
    story += [p("Three batting examples", styles["h2"])]
    story += [p(
        "Tristan Stubbs leads the eligible batter list with a 90.13 robust score. He faced 516 pressure balls across 34 pressure innings, with a shrunk pressure strike rate of 181.06 and a 68.99-point uplift over his normal rate. Liam Livingstone and Shreyas Iyer follow; both combined high pressure strike rates with large uplifts and substantial samples. Rinku Singh sits fifth, but his 689 pressure balls and 49 innings give the ranking a strong volume signal.",
        styles["body"],
    )]
    story += [p("Three bowling examples", styles["h2"])]
    story += [p(
        "After the IPL eligibility filter, Akeal Hosein leads at 89.31. His pressure economy is 7.81 over 235 legal balls and he took 25 credited wickets in pressure situations. Matthew Humphreys ranks second with a 7.38 economy and 14 wickets, but from 85 pressure legal balls, so the volume deserves attention. Sunil Narine ranks third with a 6.63 pressure economy across 393 legal balls and 32 wickets.",
        styles["body"],
    )]
    story += [p("How sensitive is the order?", styles["h2"]), p(
        "Fourteen of the primary top twenty batters remain in the strict top twenty. For bowlers the overlap is seven of twenty. The batting shortlist is steadier under the two pressure definitions; bowling positions move more. Use the exact score order as a starting point, and read the sample volumes before treating adjacent ranks as meaningfully different.",
        styles["body"],
    )]
    story += [p("Limits and next checks", styles["h2"]), p(
        "This is a historical pressure-performance screen, not a full scouting grade. The pack does not give us auction price, current availability, injury status, role certainty, venue adjustment or opponent strength. T20I results add international evidence but are not a substitute for IPL role fit. Before a bid, RR would still need to check the live auction pool, role balance, overseas slots and budget. A score cannot tell the franchise what to pay.",
        styles["body"],
    )]
    story += [p("Reproducibility", styles["h2"]), p(
        "The analysis is implemented in pressure_rankings.py, robust_rankings.py, sensitivity_check.py and continuous_pressure_rankings.py. The report tables come from robust_batting_rankings.csv and the IPL-filtered auction_ready_bowling_rankings.csv. The companion dashboard shows the same ordered lists and opens a short selection explanation when a player card is clicked.",
        styles["small"],
    )]
    story += [p(
        "Sources: Rajasthan Royals SupeRR Selector Season 2 data pack (competitions.csv, matches.csv, ball_by_ball.csv) and the Unstop Round 1 challenge brief. Match counts and scores in this report are calculated from the supplied files.",
        styles["small"],
    )]

    doc.build(story, onFirstPage=footer, onLaterPages=footer)
    print(OUT)


if __name__ == "__main__":
    main()
