-- Longueur des relais par composé : moyenne, extrêmes, et le relais le plus long
-- (pilote, tours) grâce à ROW_NUMBER. Le dernier relais de chaque pilote est
-- marqué séparément : il est souvent écourté par l'arrivée, pas par l'usure.
WITH stint_len AS (
    SELECT
        s.circuit,
        st.driver_number,
        d.acronym,
        st.stint_number,
        st.compound,
        st.lap_end - st.lap_start + 1 AS n_laps,
        st.stint_number = MAX(st.stint_number) OVER (
            PARTITION BY st.session_key, st.driver_number) AS is_final_stint
    FROM stints st
    JOIN sessions s USING (session_key)
    JOIN drivers d ON d.session_key = st.session_key AND d.driver_number = st.driver_number
    WHERE st.compound IN ('SOFT', 'MEDIUM', 'HARD')
),
ranked AS (
    SELECT *,
           ROW_NUMBER() OVER (PARTITION BY circuit, compound ORDER BY n_laps DESC) AS rk
    FROM stint_len
)
SELECT
    circuit,
    compound,
    COUNT(*)                                       AS n_stints,
    ROUND(AVG(n_laps), 1)                          AS avg_laps,
    ROUND(AVG(CASE WHEN NOT is_final_stint THEN n_laps END), 1) AS avg_laps_ended_by_pit,
    MIN(n_laps)                                    AS min_laps,
    MAX(n_laps)                                    AS max_laps,
    MAX(CASE WHEN rk = 1 THEN acronym END)         AS longest_by
FROM ranked
GROUP BY circuit, compound
ORDER BY circuit, avg_laps DESC;
