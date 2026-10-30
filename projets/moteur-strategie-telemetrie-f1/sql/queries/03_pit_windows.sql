-- Fenêtres d'arrêt : tour moyen et part de la course du 1er et du 2e arrêt, longueur du relais qui se termine.
WITH stops AS (
    SELECT
        s.circuit,
        s.total_laps,
        p.driver_number,
        p.lap_number,
        p.lane_duration_s,
        ROW_NUMBER() OVER w AS stop_no,
        p.lap_number - COALESCE(LAG(p.lap_number) OVER w, 0) AS laps_since_prev_stop
    FROM pit_stops p
    JOIN sessions s USING (session_key)
    WINDOW w AS (PARTITION BY p.session_key, p.driver_number ORDER BY p.lap_number)
)
SELECT
    circuit,
    stop_no,
    COUNT(*)                                          AS n_stops,
    MIN(lap_number)                                   AS first_lap,
    ROUND(AVG(lap_number), 1)                         AS avg_lap,
    MAX(lap_number)                                   AS last_lap,
    ROUND(100.0 * AVG(lap_number) / MAX(total_laps))  AS avg_pct_race,
    ROUND(AVG(laps_since_prev_stop), 1)               AS avg_stint_before,
    ROUND(AVG(lane_duration_s), 1)                    AS avg_lane_time_s
FROM stops
GROUP BY circuit, stop_no
HAVING COUNT(*) >= 2
ORDER BY circuit, stop_no;
