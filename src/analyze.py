"""Load the home-game CSV into SQLite, run the SQL checks, compute medians, and chart each game.

SQLite has no MEDIAN, so medians are computed in pandas.
Writes output/median_summary.csv, output/attendance_by_game.png and docs/index.html
(the interactive page, built from src/dashboard_template.html).
Usage: python src/analyze.py
"""
import json
import sqlite3
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.lines import Line2D
from matplotlib.patches import FancyBboxPatch, Patch

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "mercury_2026_home_games.csv"
OUT = ROOT / "output"
DOCS = ROOT / "docs"
TEMPLATE = ROOT / "src" / "dashboard_template.html"
CAPACITY = 17071
TITLE = "Phoenix Mercury 2026 home attendance"
# Mercury-inspired violet + orange; this pair passes colorblind-separation and contrast checks.
ACCENT, FLAG, REST = "#6250d6", "#eb6834", "#cfcec7"
INK, INK2, MUTED, GRID, SURFACE = "#0b0b0b", "#52514e", "#898781", "#e1e0d9", "#fcfcfb"


def prep_games(df):
    """Games in date order with short date labels and a top-3 flag."""
    games = df.sort_values("date").reset_index(drop=True)
    d = pd.to_datetime(games["date"])
    games["day"] = d.dt.day.astype(str)
    games["label"] = d.dt.strftime("%b ") + games["day"]
    games["top3"] = games.index.isin(games["attendance"].nlargest(3).index)
    return games


def plot_png(games, median):
    plt.rcParams.update({"font.family": ["Helvetica Neue", "Helvetica", "Arial", "DejaVu Sans"]})
    fig, ax = plt.subplots(figsize=(12, 6.2), facecolor=SURFACE)
    ax.set_facecolor(SURFACE)
    n, bw = len(games), 0.62
    for i, g in games.iterrows():
        ax.add_patch(FancyBboxPatch((i - bw / 2, 0), bw, g["attendance"], mutation_aspect=900,
                                    boxstyle="round,pad=0,rounding_size=0.12",
                                    facecolor=ACCENT if g["top3"] else REST, edgecolor="none"))
        # square off the rounded bottom so bars sit flat on the baseline
        ax.add_patch(plt.Rectangle((i - bw / 2, 0), bw, 400, facecolor=ACCENT if g["top3"] else REST, edgecolor="none"))
        if g["flag"]:
            ax.scatter(i, g["attendance"] + 450, s=42, color=FLAG, edgecolor=SURFACE, linewidth=1.5, zorder=4)
        if g["top3"]:
            text = "Sellout" if g["attendance"] >= CAPACITY else f"{g['attendance']:,}"
            ax.text(i, g["attendance"] + (900 if g["attendance"] >= CAPACITY else 350), text,
                    ha="center", va="bottom", fontsize=10, fontweight="bold", color=INK, zorder=5,
                    bbox=dict(facecolor=SURFACE, edgecolor="none", pad=1.5))

    ax.axhline(CAPACITY, color=MUTED, linestyle=(0, (4, 4)), linewidth=1, zorder=3)
    ax.axhline(median, color=INK2, linewidth=1.4, zorder=3)
    ax.text(n - 0.4, CAPACITY + 250, f"Capacity {CAPACITY:,}", ha="right", fontsize=9.5, color=MUTED)
    ax.text(n - 0.4, median + 250, f"Median {median:,.0f}", ha="right", fontsize=9.5, color=INK2, zorder=5,
            bbox=dict(facecolor=SURFACE, edgecolor="none", pad=1.5))

    split = games.index[~games["month"].isin(["May", "Jun"])][0] - 0.5
    ax.axvline(split, color=GRID, linewidth=1, zorder=0)
    ax.text(split - 0.2, 18900, "May–June", ha="right", fontsize=9.5, color=INK2)
    ax.text(split + 0.2, 18900, "July–Sept", ha="left", fontsize=9.5, color=INK2)

    ax.set_xlim(-0.6, n - 0.4)
    ax.set_ylim(0, 19800)
    ax.set_yticks(range(0, 15001, 5000), ["0", "5K", "10K", "15K"])
    ax.yaxis.grid(True, color=GRID, linewidth=1)
    ax.set_axisbelow(True)
    ax.set_xticks(range(n), games["day"])
    ax.tick_params(length=0, colors=MUTED, labelsize=9.5)
    months = games.drop_duplicates("month")
    for i, g in months.iterrows():
        ax.text(i - bw / 2, -1500, g["month"], fontsize=10, color=INK2, ha="left", va="top")
    for s in ("top", "right", "left"):
        ax.spines[s].set_visible(False)
    ax.spines["bottom"].set_color("#c3c2b7")

    fig.text(0.035, 0.955, TITLE, fontsize=17, fontweight="bold", color=INK)
    fig.text(0.035, 0.912, f"Announced attendance at all 22 home games. Typical crowd {median:,.0f}, "
             f"{median / CAPACITY:.0%} of capacity; crowds grew in July–Sept despite a 16-28 season.",
             fontsize=11, color=INK2)
    fig.legend(handles=[Patch(color=ACCENT, label="Three largest crowds"),
                        Patch(color=REST, label="Other games"),
                        Line2D([], [], marker="o", linestyle="none", markersize=7, markerfacecolor=FLAG,
                               markeredgecolor=SURFACE, label="Repeated official figure (confirmed on WNBA.com)")],
               loc="lower left", bbox_to_anchor=(0.03, 0.0), ncol=3, frameon=False, fontsize=10,
               labelcolor=INK2, handlelength=1.2)
    fig.subplots_adjust(left=0.05, right=0.985, top=0.85, bottom=0.17)
    fig.savefig(OUT / "attendance_by_game.png", dpi=150, facecolor=SURFACE)
    plt.close(fig)


def build_dashboard(games):
    cols = ["date", "day", "label", "month", "weekday", "weekend", "opponent", "opp_playoff",
            "result", "attendance", "pct_capacity", "record_going_in", "flag"]
    rows = games[cols].rename(columns={"pct_capacity": "pct", "record_going_in": "record"}).to_dict("records")
    payload = json.dumps({"capacity": CAPACITY, "games": rows}).replace("<", "\\u003c")
    DOCS.mkdir(exist_ok=True)
    (DOCS / "index.html").write_text(TEMPLATE.read_text().replace("__DATA__", payload))


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
    build_dashboard(games)
    print(f"\nWrote {OUT / 'attendance_by_game.png'} and {DOCS / 'index.html'}")


if __name__ == "__main__":
    main()
