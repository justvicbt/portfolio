-- Rythme moyen par composé et par course sur les tours propres, corrigé du carburant, écart au plus rapide.
WITH corrected AS (
    SELECT
        s.circuit,
        l.compound,
        l.lap_time_s - 0.03 * 100 * (1 - (l.lap_number - 0.5) / s.total_laps) AS fuel_corr_s
    FROM laps l
    JOIN sessions s USING (session_key)
    WHERE l.is_clean = 1
),
by_compound AS (
    SELECT circuit, compound, COUNT(*) AS n_laps, AVG(fuel_corr_s) AS avg_fuel_corr_s
    FROM corrected
    GROUP BY circuit, compound
)
SELECT
    circuit,
    compound,
    n_laps,
    ROUND(avg_fuel_corr_s, 3) AS avg_fuel_corr_s,
    ROUND(avg_fuel_corr_s - MIN(avg_fuel_corr_s) OVER (PARTITION BY circuit), 3) AS gap_to_fastest_s
FROM by_compound
ORDER BY circuit, avg_fuel_corr_s;
-- Attention : moyenne brute, sans effet pilote ; un composé utilisé surtout en tête paraît plus rapide (voir degradation.py).
