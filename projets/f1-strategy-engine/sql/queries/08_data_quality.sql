-- Audit du nettoyage : combien de tours gardés par course, et pour quelle raison
-- les autres sont écartés. À lire avant de croire n'importe quel chiffre du modèle.
WITH counts AS (
    SELECT s.circuit, COALESCE(l.exclusion, 'clean') AS reason, COUNT(*) AS n_laps
    FROM laps l
    JOIN sessions s USING (session_key)
    GROUP BY s.circuit, COALESCE(l.exclusion, 'clean')
)
SELECT
    circuit,
    reason,
    n_laps,
    ROUND(100.0 * n_laps / SUM(n_laps) OVER (PARTITION BY circuit), 1) AS pct_of_race
FROM counts
ORDER BY circuit, n_laps DESC;
