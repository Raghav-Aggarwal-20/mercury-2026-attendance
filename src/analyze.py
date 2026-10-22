"""Load the home-game CSV into SQLite, run the SQL checks, and compute medians.

SQLite has no MEDIAN, so medians are computed in pandas.
Usage: python src/analyze.py
"""
import sqlite3
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "mercury_2026_home_games.csv"
OUT = ROOT / "output"


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
          "median_pct_capacity": round(g["attendance"].median() / 17071 * 100, 1)} for k, g in cuts.items()]
    )
    OUT.mkdir(exist_ok=True)
    summary.to_csv(OUT / "median_summary.csv", index=False)
    print("\n-- medians")
    print(summary.to_string(index=False))


if __name__ == "__main__":
    main()
