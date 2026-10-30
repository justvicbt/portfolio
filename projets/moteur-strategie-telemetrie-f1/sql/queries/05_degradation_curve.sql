-- Courbe de dégradation brute : écart aux 3 premiers tours propres du relais, par composé et tranche de 5 tours d'âge.
WITH corrected AS (
    SELECT
        s.circuit, l.session_key, l.driver_number, l.stint_number, l.compound, l.tyre_age,
        l.lap_time_s - 0.03 * 100 * (1 - (l.lap_number - 0.5) / s.total_laps) AS fuel_corr_s,
        ROW_NUMBER() OVER (PARTITION BY l.session_key, l.driver_number, l.stint_number
                           ORDER BY l.lap_number) AS nth_clean_lap
    FROM laps l
    JOIN sessions s USING (session_key)
    WHERE l.is_clean = 1
),
baseline AS (
    SELECT *,
           AVG(CASE WHEN nth_clean_lap <= 3 THEN fuel_corr_s END)
               OVER (PARTITION BY session_key, driver_number, stint_number) AS stint_base_s,
           COUNT(*) OVER (PARTITION BY session_key, driver_number, stint_number) AS n_clean_in_stint
    FROM corrected
)
SELECT
    circuit,
    compound,
    (tyre_age / 5) * 5                         AS tyre_age_from,
    (tyre_age / 5) * 5 + 4                     AS tyre_age_to,
    COUNT(*)                                   AS n_laps,
    ROUND(AVG(fuel_corr_s - stint_base_s), 3)  AS avg_delta_vs_stint_start_s
FROM baseline
WHERE n_clean_in_stint >= 8
GROUP BY circuit, compound, tyre_age / 5
HAVING COUNT(*) >= 10
ORDER BY circuit, compound, tyre_age_from;
