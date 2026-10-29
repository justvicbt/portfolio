-- Temps réellement perdu par un arrêt : (tour d'entrée + tour de sortie)
-- moins deux tours "normaux" du même pilote. Le tour normal de référence est
-- la moyenne de ses tours propres dans les 5 tours avant/après l'arrêt.
-- C'est le paramètre clé du simulateur 1 arrêt vs 2 arrêts.
-- Le tour de sortie peut être absent ou sous SC : on ne garde que les arrêts
-- sous drapeau vert, sinon la perte est sous-estimée.
WITH pit_pairs AS (
    SELECT
        p.session_key,
        p.driver_number,
        p.lap_number,
        lin.lap_time_s  AS in_lap_s,
        lout.lap_time_s AS out_lap_s
    FROM pit_stops p
    JOIN laps lin  ON lin.session_key = p.session_key AND lin.driver_number = p.driver_number
                  AND lin.lap_number = p.lap_number
    JOIN laps lout ON lout.session_key = p.session_key AND lout.driver_number = p.driver_number
                  AND lout.lap_number = p.lap_number + 1
    WHERE lin.track_status = 'GREEN' AND lout.track_status = 'GREEN'
),
reference AS (
    SELECT pp.*, AVG(l.lap_time_s) AS ref_lap_s, COUNT(l.lap_time_s) AS n_ref
    FROM pit_pairs pp
    JOIN laps l ON l.session_key = pp.session_key AND l.driver_number = pp.driver_number
               AND l.is_clean = 1 AND l.lap_number BETWEEN pp.lap_number - 5 AND pp.lap_number + 6
    GROUP BY pp.session_key, pp.driver_number, pp.lap_number
    HAVING COUNT(l.lap_time_s) >= 3
),
losses AS (
    SELECT session_key, in_lap_s + out_lap_s - 2 * ref_lap_s AS loss_s,
           ROW_NUMBER() OVER (PARTITION BY session_key ORDER BY in_lap_s + out_lap_s - 2 * ref_lap_s) AS rn,
           COUNT(*)     OVER (PARTITION BY session_key) AS n
    FROM reference
)
SELECT
    s.circuit,
    MAX(n)                       AS n_stops_used,
    ROUND(AVG(loss_s), 1)        AS avg_pit_loss_s,
    -- médiane (SQLite n'a pas PERCENTILE_CONT) : moyenne des 1 ou 2 valeurs centrales
    ROUND(AVG(CASE WHEN rn IN ((n + 1) / 2, (n + 2) / 2) THEN loss_s END), 1) AS median_pit_loss_s,
    ROUND(MIN(loss_s), 1)        AS min_s,
    ROUND(MAX(loss_s), 1)        AS max_s
FROM losses
JOIN sessions s USING (session_key)
GROUP BY s.circuit
ORDER BY median_pit_loss_s;
