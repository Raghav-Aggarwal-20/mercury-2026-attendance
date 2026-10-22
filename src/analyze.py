"""Load the home-game CSV into SQLite, run the SQL checks, compute medians, and chart each game.

SQLite has no MEDIAN, so medians are computed in pandas.
Writes output/median_summary.csv, output/attendance_by_game.png and docs/index.html.
Usage: python src/analyze.py
"""
import sqlite3
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
import plotly.graph_objects as go
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
from matplotlib.ticker import StrMethodFormatter

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "mercury_2026_home_games.csv"
OUT = ROOT / "output"
DOCS = ROOT / "docs"
CAPACITY = 17071
TITLE = "Phoenix Mercury 2026 home attendance"
BLUE, GRAY, RED = "#1f5fa8", "#b8bcc2", "#c62828"


def prep_games(df):
    """Games in date order with a short date label, bar color and outline."""
    games = df.sort_values("date").reset_index(drop=True)
    d = pd.to_datetime(games["date"])
    games["label"] = d.dt.strftime("%b ") + d.dt.day.astype(str)
    top3 = games["attendance"].nlargest(3).index
    games["color"] = GRAY
    games.loc[top3, "color"] = BLUE
    games["flagged"] = games["flag"] != ""
    return games


def plot_png(games, median):
    fig, ax = plt.subplots(figsize=(11, 5.5))
    x = range(len(games))
    ax.bar(x, games["attendance"], facecolor=list(games["color"]),
           edgecolor=[RED if f else "none" for f in games["flagged"]],
           linewidth=[1.8 if f else 0 for f in games["flagged"]])
    ax.axhline(CAPACITY, color="black", linestyle="--", linewidth=1)
    ax.axhline(median, color="black", linewidth=1)
    ax.text(len(games) - 0.5, CAPACITY, f"Capacity ({CAPACITY:,})", ha="right", va="bottom", fontsize=9)
    ax.text(len(games) - 0.5, median, f"Median ({median:,.0f})", ha="right", va="bottom", fontsize=9)
    ax.set_xticks(list(x), games["label"], rotation=45, ha="right")
    ax.set_xlim(-0.6, len(games) - 0.4)
    ax.set_ylim(0, CAPACITY * 1.08)
    ax.yaxis.set_major_formatter(StrMethodFormatter("{x:,.0f}"))
    ax.set_ylabel("Announced attendance")
    ax.set_title(TITLE, loc="left", fontsize=13, fontweight="bold")
    ax.spines[["top", "right"]].set_visible(False)
    ax.legend(handles=[Patch(color=BLUE, label="Three largest crowds"),
                       Patch(color=GRAY, label="Other games"),
                       Patch(facecolor="white", edgecolor=RED, linewidth=1.8, label="Repeated official figure"),
                       Line2D([], [], color="black", linestyle="--", linewidth=1, label="Capacity"),
                       Line2D([], [], color="black", linewidth=1, label="Median")],
              loc="upper left", fontsize=8, frameon=False, ncol=5, bbox_to_anchor=(0, -0.14))
    fig.tight_layout()
    fig.savefig(OUT / "attendance_by_game.png", dpi=150)
    plt.close(fig)


def plot_html(games, median):
    hover = [f"<b>{r.label} vs {r.opponent}</b> ({r.result})<br>{r.weekday}, {r.opp_playoff}<br>"
             f"Attendance: {r.attendance:,} ({r.pct_capacity:.1f}% of capacity)<br>Record going in: {r.record_going_in}"
             + (f"<br><span style='color:{RED}'>{r.flag}</span>" if r.flagged else "")
             for r in games.itertuples()]
    fig = go.Figure(go.Bar(
        x=games["label"], y=games["attendance"], marker_color=games["color"],
        marker_line_color=[RED if f else "rgba(0,0,0,0)" for f in games["flagged"]],
        marker_line_width=[2 if f else 0 for f in games["flagged"]],
        hovertext=hover, hoverinfo="text"))
    label = dict(annotation_position="top right", annotation_bgcolor="rgba(255,255,255,0.8)")
    fig.add_hline(y=CAPACITY, line_dash="dash", line_width=1, annotation_text=f"Capacity ({CAPACITY:,})", **label)
    fig.add_hline(y=median, line_width=1, annotation_text=f"Median ({median:,.0f})", **label)
    fig.update_layout(
        yaxis=dict(title="Announced attendance", tickformat=",", range=[0, CAPACITY * 1.08]),
        xaxis=dict(type="category", tickangle=-45),
        template="plotly_white", showlegend=False, autosize=True, height=480,
        margin=dict(t=20, r=10, l=60, b=70))
    chart = fig.to_html(full_html=False, include_plotlyjs="cdn", div_id="chart",
                        config={"displaylogo": False, "responsive": True})
    DOCS.mkdir(exist_ok=True)
    (DOCS / "index.html").write_text(f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Mercury 2026 Attendance</title>
<style>
  body {{ margin: 0; background: #fff; color: #1d1d1f; font: 16px/1.5 -apple-system, "Segoe UI", Roboto, sans-serif; }}
  main {{ max-width: 1000px; margin: 0 auto; padding: 24px 16px; }}
  h1 {{ font-size: 1.5rem; margin: 0 0 4px; }}
  p {{ margin: 0 0 12px; color: #555; }}
  .key span {{ display: inline-block; width: 12px; height: 12px; margin: 0 4px -1px 12px; }}
  .key span:first-child {{ margin-left: 0; }}
  a {{ color: {BLUE}; }}
</style>
</head>
<body>
<main>
  <h1>{TITLE}</h1>
  <p>Announced attendance for all 22 regular-season home games, in date order. Hover or tap a bar for details.</p>
  <p class="key"><span style="background:{BLUE}"></span>Three largest crowds
    <span style="background:{GRAY}"></span>Other games
    <span style="background:{GRAY};outline:2px solid {RED};outline-offset:-2px"></span>Repeated official figure (confirmed on WNBA.com)</p>
  {chart}
  <p>Source: 2026 Phoenix Mercury season game log, checked against WNBA.com box scores.
    Code and full write-up: <a href="https://github.com/Raghav-Aggarwal-20/mercury-2026-attendance">GitHub repo</a>.</p>
</main>
</body>
</html>
""")


def main():
    df = pd.read_csv(DATA, dtype={"flag": str}).fillna({"flag": ""})
    con = sqlite3.connect(":memory:")
    con.executescript((ROOT / "sql" / "schema.sql").read_text())
    df.to_sql("home_games", con, if_exists="append", index=False)

    for i, stmt in enumerate(s for s in (ROOT / "sql" / "analysis.sql").read_text().split(";") if s.strip()):
        print(f"\n-- query {i + 1}")
        print(pd.read_sql(stmt, con).to_string(index=False))

    df["part"] = df["month"].map(lambda m: "May-June" if m in ("May", "Jun") else "July-Sept")
    cuts = {"All games": df}
    for col in ("weekend", "opp_playoff", "part"):
        for k, g in df.groupby(col):
            cuts[k] = g
    summary = pd.DataFrame(
        [{"segment": k, "games": len(g), "median_attendance": g["attendance"].median(),
          "median_pct_capacity": round(g["attendance"].median() / CAPACITY * 100, 1)} for k, g in cuts.items()]
    )
    OUT.mkdir(exist_ok=True)
    summary.to_csv(OUT / "median_summary.csv", index=False)
    print("\n-- medians")
    print(summary.to_string(index=False))

    games = prep_games(df)
    median = df["attendance"].median()
    plot_png(games, median)
    plot_html(games, median)
    print(f"\nWrote {OUT / 'attendance_by_game.png'} and {DOCS / 'index.html'}")


if __name__ == "__main__":
    main()
