-- Télémétrie par secteur sur le tour le plus rapide de chaque pilote :
-- vitesse moyenne, part du temps à fond (accélérateur >= 98 %), part du temps
-- au freinage et part avec le DRS ouvert (codes OpenF1 10, 12, 14).
-- Les échantillons sont réguliers (~3,7 Hz), donc "part des échantillons"
-- ≈ "part du temps". RANK classe les pilotes par vitesse moyenne dans le secteur.
WITH per_sector AS (
    SELECT
        s.circuit,
        d.acronym,
        t.sector,
        COUNT(*)                                          AS n_samples,
        AVG(t.speed_kmh)                                  AS avg_speed,
        AVG(CASE WHEN t.throttle_pct >= 98 THEN 1.0 ELSE 0 END) AS full_throttle_share,
        AVG(t.brake_on * 1.0)                             AS braking_share,
        AVG(CASE WHEN t.drs >= 10 THEN 1.0 ELSE 0 END)    AS drs_open_share
    FROM telemetry t
    JOIN sessions s USING (session_key)
    JOIN drivers d ON d.session_key = t.session_key AND d.driver_number = t.driver_number
    GROUP BY s.circuit, d.acronym, t.sector
)
SELECT
    circuit,
    sector,
    acronym,
    ROUND(avg_speed, 1)                    AS avg_speed_kmh,
    ROUND(100 * full_throttle_share, 1)    AS full_throttle_pct,
    ROUND(100 * braking_share, 1)          AS braking_pct,
    ROUND(100 * drs_open_share, 1)         AS drs_open_pct,
    RANK() OVER (PARTITION BY circuit, sector ORDER BY avg_speed DESC) AS speed_rank
FROM per_sector
WHERE n_samples >= 20
ORDER BY circuit, sector, speed_rank;
