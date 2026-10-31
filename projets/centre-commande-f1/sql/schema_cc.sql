-- Tables propres à ce projet, ajoutées au schéma du moteur de stratégie ; base reconstruite à chaque ETL (DROP voulus).
-- Exécuté AVANT le schéma du moteur de stratégie : SQLite refuse de supprimer une table parente encore référencée.

DROP TABLE IF EXISTS etl_checks;
DROP TABLE IF EXISTS lap_conditions;
DROP TABLE IF EXISTS results;
DROP TABLE IF EXISTS weather;

-- Mesures météo validées (environ une par minute), valeurs hors plage remplacées par NULL.
CREATE TABLE weather (
    session_key        INTEGER NOT NULL REFERENCES sessions (session_key),
    date               TEXT    NOT NULL,
    air_temp_c         REAL CHECK (air_temp_c BETWEEN -10 AND 50),
    track_temp_c       REAL CHECK (track_temp_c BETWEEN 5 AND 70),
    humidity_pct       REAL CHECK (humidity_pct BETWEEN 0 AND 100),
    pressure_hpa       REAL CHECK (pressure_hpa BETWEEN 800 AND 1100),
    wind_speed_ms      REAL CHECK (wind_speed_ms BETWEEN 0 AND 40),
    wind_direction_deg REAL CHECK (wind_direction_deg BETWEEN 0 AND 360),
    rainfall           INTEGER CHECK (rainfall IN (0, 1)),
    PRIMARY KEY (session_key, date)
);

-- Classement officiel OpenF1, contrôle des positions recalculées.
CREATE TABLE results (
    session_key    INTEGER NOT NULL,
    driver_number  INTEGER NOT NULL,
    position       INTEGER CHECK (position >= 1),
    number_of_laps INTEGER CHECK (number_of_laps >= 0),
    status         TEXT    NOT NULL CHECK (status IN ('FINISHED', 'DNF', 'DNS', 'DSQ')),
    points         REAL    CHECK (points >= 0),
    PRIMARY KEY (session_key, driver_number),
    FOREIGN KEY (session_key, driver_number) REFERENCES drivers (session_key, driver_number)
);

-- Une ligne par tour : position et écart recalculés aux passages sur la ligne, météo au milieu du tour.
CREATE TABLE lap_conditions (
    session_key     INTEGER NOT NULL,
    driver_number   INTEGER NOT NULL,
    lap_number      INTEGER NOT NULL,
    lap_end         TEXT,
    timing_repaired INTEGER NOT NULL DEFAULT 0 CHECK (timing_repaired IN (0, 1)),
    position        INTEGER CHECK (position >= 1),
    gap_to_leader_s REAL    CHECK (gap_to_leader_s >= 0),
    air_temp_c      REAL,
    track_temp_c    REAL,
    humidity_pct    REAL,
    wind_speed_ms   REAL,
    rain            INTEGER CHECK (rain IN (0, 1)),
    weather_status  TEXT    NOT NULL CHECK (weather_status IN ('measured', 'interpolated', 'missing')),
    PRIMARY KEY (session_key, driver_number, lap_number),
    FOREIGN KEY (session_key, driver_number, lap_number)
        REFERENCES laps (session_key, driver_number, lap_number)
);

-- Résultats des contrôles de cohérence de l'ETL, affichés dans le tableau de bord.
CREATE TABLE etl_checks (
    session_key INTEGER NOT NULL REFERENCES sessions (session_key),
    check_name  TEXT    NOT NULL,
    status      TEXT    NOT NULL CHECK (status IN ('ok', 'warning', 'fail')),
    value       REAL,
    detail      TEXT    NOT NULL,
    PRIMARY KEY (session_key, check_name)
);

CREATE INDEX idx_weather_date       ON weather (session_key, date);
CREATE INDEX idx_conditions_lap     ON lap_conditions (session_key, lap_number);
