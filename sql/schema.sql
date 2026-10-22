-- One row per 2026 Phoenix Mercury regular-season home game.
CREATE TABLE IF NOT EXISTS home_games (
    home_game        INTEGER PRIMARY KEY,
    date             TEXT NOT NULL,      -- YYYY-MM-DD
    month            TEXT,
    weekday          TEXT,
    weekend          TEXT,               -- 'Weekend' = Fri-Sun
    opponent         TEXT NOT NULL,
    opp_playoff      TEXT,               -- from 2026 final standings
    result           TEXT CHECK (result IN ('W','L')),
    attendance       INTEGER NOT NULL,
    capacity         INTEGER NOT NULL,
    pct_capacity     REAL,
    record_going_in  TEXT,
    flag             TEXT                -- 'Repeated official figure' where the number needs verifying
);
