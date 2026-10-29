-- Temps perdu par chaque arrêt sous drapeau vert, un arrêt par ligne.
-- Même définition que 04_pit_loss.sql du projet 1, sans l'agrégation finale :
-- (tour d'entrée + tour de sortie) - 2 x tour normal du même pilote, le tour normal
-- étant la moyenne de ses tours propres dans les 5 tours avant/après l'arrêt.
-- Le simulateur rééchantillonne ces arrêts : la queue (arrêts ratés) est conservée.
WITH pit_pairs AS (
    SELECT p.session_key, p.driver_number, p.lap_number,
           lin.lap_time_s AS in_lap_s, lout.lap_time_s AS out_lap_s
    FROM pit_stops p
    JOIN laps lin  ON lin.session_key = p.session_key AND lin.driver_number = p.driver_number
                  AND lin.lap_number = p.lap_number
    JOIN laps lout ON lout.session_key = p.session_key AND lout.driver_number = p.driver_number
                  AND lout.lap_number = p.lap_number + 1
    WHERE lin.track_status = 'GREEN' AND lout.track_status = 'GREEN'
),
reference AS (
    SELECT pp.*, AVG(l.lap_time_s) AS ref_lap_s
    FROM pit_pairs pp
    JOIN laps l ON l.session_key = pp.session_key AND l.driver_number = pp.driver_number
               AND l.is_clean = 1 AND l.lap_number BETWEEN pp.lap_number - 5 AND pp.lap_number + 6
    GROUP BY pp.session_key, pp.driver_number, pp.lap_number
    HAVING COUNT(l.lap_time_s) >= 3
)
SELECT s.circuit, d.acronym AS driver, r.lap_number,
       r.in_lap_s + r.out_lap_s - 2 * r.ref_lap_s AS loss_s
FROM reference r
JOIN sessions s USING (session_key)
JOIN drivers d ON d.session_key = r.session_key AND d.driver_number = r.driver_number
ORDER BY s.circuit, r.lap_number;
