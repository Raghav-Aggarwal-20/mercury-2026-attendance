-- Season totals
SELECT COUNT(*) AS games,
       ROUND(AVG(attendance)) AS avg_attendance,
       SUM(attendance < 10000) AS games_under_10k,
       SUM(attendance >= capacity) AS sellouts
FROM home_games;

-- Attendance figures that appear more than once (data-quality check)
SELECT attendance, COUNT(*) AS times, GROUP_CONCAT(date || ' ' || opponent, ' | ') AS games
FROM home_games
GROUP BY attendance
HAVING COUNT(*) > 1;

-- Average attendance and win count by part of season
SELECT CASE WHEN month IN ('May','Jun') THEN 'May-June' ELSE 'July-Sept' END AS part_of_season,
       COUNT(*) AS games,
       SUM(result = 'W') AS wins,
       ROUND(AVG(attendance)) AS avg_attendance
FROM home_games
GROUP BY part_of_season;

-- Average attendance by opponent type and by day type
SELECT 'opponent' AS cut, opp_playoff AS segment, COUNT(*) AS games, ROUND(AVG(attendance)) AS avg_attendance
FROM home_games GROUP BY opp_playoff
UNION ALL
SELECT 'day', weekend, COUNT(*), ROUND(AVG(attendance))
FROM home_games GROUP BY weekend;
