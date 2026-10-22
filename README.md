# Phoenix Mercury 2026 home attendance

![Announced attendance by home game](output/attendance_by_game.png)

A look at announced attendance for the Mercury's 22 regular-season home games in 2026, to see what moved crowds in a 16-28 season.

Interactive version: https://raghav-aggarwal-20.github.io/mercury-2026-attendance/

## Findings

- The median home crowd was 10,390, or 60.9% of the 17,071 basketball capacity. The average was 11,128. Three games (Indiana on July 9, Portland on August 16, Connecticut on July 19) pulled the average above the median.
- Opponent standings had little effect. The median against 2026 playoff teams was 10,459. Against non-playoff teams it was 10,321.
- Star power is harder to read. August 16 vs Portland, the first home game after Kelsey Plum's Phoenix debut, drew 16,513 even though she sat out injured. Her only home appearance, August 25 vs Washington, drew 10,459. August 16 was also a Sunday, so the day and the timing of ticket purchases may explain more than who played.
- Crowds grew while results did not. The May-June median was 9,500 over 8 games (2 wins). The July-September median was 11,079 over 14 games (5 wins).
- Fri-Sun games had a median of 11,094. Mon-Thu games had 10,152.
- The league reported 9,234 for three June home games (June 1, 13 and 17). The July 17 figure (10,321) matches the Mercury's road crowd in Las Vegas on July 11. I checked all four against the WNBA.com box scores and they match. A scan count is unlikely to repeat exactly, so I treat these as reported figures and lean on medians and the July-September games for the trend. The four rows are flagged in the data.

## Data

`data/mercury_2026_home_games.csv` has one row per home game. Attendance, opponent, result and record come from the game log on the [2026 Phoenix Mercury season](https://en.wikipedia.org/wiki/2026_Phoenix_Mercury_season) Wikipedia page. I checked the four repeated figures against WNBA.com box scores. I added weekday, Fri-Sun vs Mon-Thu, opponent playoff status from final standings, percent of capacity, and the data-quality flag.

Attendance is the announced figure. It does not separate paid, distributed and scanned tickets.

## Run it

```
pip install -r requirements.txt
python src/analyze.py
```

The script loads the CSV into SQLite with `sql/schema.sql`, runs the queries in `sql/analysis.sql` (totals, repeated figures, splits), and writes medians to `output/median_summary.csv`. It also draws the chart above to `output/attendance_by_game.png` and writes the interactive version to `docs/index.html`, which GitHub Pages serves. Medians are computed in pandas because SQLite has no median function.

## What would come next with internal data

- Paid vs. distributed vs. scanned tickets per game
- Season ticket member share of each crowd
- Average price paid and promotion-night flags
- Secondary-market resale volume per game
