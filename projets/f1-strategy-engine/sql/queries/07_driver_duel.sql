-- Duel entre deux pilotes sur une course : temps au tour, pneus, et écart cumulé
-- (SUM ... OVER) tour après tour. Un écart positif = pilote 1 devant.
-- Changer les paramètres dans la CTE `params`.
WITH params AS (
    SELECT 'Hungaroring' AS circuit, 'NOR' AS driver_1, 'PIA' AS driver_2
),
duel AS (
    SELECT
        l.lap_number,
        MAX(CASE WHEN d.acronym = p.driver_1 THEN l.lap_time_s END) AS lap_1_s,
        MAX(CASE WHEN d.acronym = p.driver_2 THEN l.lap_time_s END) AS lap_2_s,
        MAX(CASE WHEN d.acronym = p.driver_1 THEN l.compound || ' (' || l.tyre_age || ')' END) AS tyre_1,
        MAX(CASE WHEN d.acronym = p.driver_2 THEN l.compound || ' (' || l.tyre_age || ')' END) AS tyre_2,
        MAX(l.track_status) AS track_status
    FROM laps l
    JOIN sessions s USING (session_key)
    JOIN drivers d ON d.session_key = l.session_key AND d.driver_number = l.driver_number
    JOIN params p ON s.circuit = p.circuit AND d.acronym IN (p.driver_1, p.driver_2)
    GROUP BY l.lap_number
)
SELECT
    lap_number,
    tyre_1,
    tyre_2,
    ROUND(lap_1_s, 3)                                         AS lap_1_s,
    ROUND(lap_2_s, 3)                                         AS lap_2_s,
    ROUND(lap_2_s - lap_1_s, 3)                               AS delta_lap_s,
    ROUND(SUM(lap_2_s - lap_1_s) OVER (ORDER BY lap_number), 3) AS cumulative_gap_s,
    track_status
FROM duel
WHERE lap_1_s IS NOT NULL AND lap_2_s IS NOT NULL
ORDER BY lap_number;
-- L'écart cumulé part de zéro : il ignore l'écart sur la grille de départ, et le
-- tour 1 (départ arrêté) pèse beaucoup. C'est une comparaison de rythme, pas un
-- classement exact.
