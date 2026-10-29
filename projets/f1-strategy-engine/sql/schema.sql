-- Schéma de la base F1 (SQLite, SQL volontairement standard).
-- La base est entièrement reconstruite à chaque ingestion : les DROP sont voulus.
-- Les clés suivent celles d'OpenF1 (session_key, driver_number, lap_number).

DROP TABLE IF EXISTS telemetry;
DROP TABLE IF EXISTS laps;
DROP TABLE IF EXISTS pit_stops;
DROP TABLE IF EXISTS stints;
DROP TABLE IF EXISTS race_control;
DROP TABLE IF EXISTS drivers;
DROP TABLE IF EXISTS sessions;

-- Une ligne par course chargée.
CREATE TABLE sessions (
    session_key   INTEGER PRIMARY KEY,
    meeting_key   INTEGER NOT NULL,
    year          INTEGER NOT NULL CHECK (year >= 2023),
    circuit       TEXT    NOT NULL,
    country       TEXT    NOT NULL,
    date_start    TEXT    NOT NULL,              -- ISO 8601, UTC
    total_laps    INTEGER NOT NULL CHECK (total_laps > 0)
);

CREATE TABLE drivers (
    session_key   INTEGER NOT NULL REFERENCES sessions (session_key),
    driver_number INTEGER NOT NULL,
    acronym       TEXT    NOT NULL,
    full_name     TEXT,
    team          TEXT,
    PRIMARY KEY (session_key, driver_number)
);

-- Relais : un train de pneus entre deux arrêts.
CREATE TABLE stints (
    session_key       INTEGER NOT NULL,
    driver_number     INTEGER NOT NULL,
    stint_number      INTEGER NOT NULL CHECK (stint_number >= 1),
    compound          TEXT    NOT NULL
        CHECK (compound IN ('SOFT', 'MEDIUM', 'HARD', 'INTERMEDIATE', 'WET', 'UNKNOWN')),
    lap_start         INTEGER NOT NULL CHECK (lap_start >= 1),
    lap_end           INTEGER NOT NULL,
    tyre_age_at_start INTEGER NOT NULL CHECK (tyre_age_at_start >= 0),
    PRIMARY KEY (session_key, driver_number, stint_number),
    FOREIGN KEY (session_key, driver_number) REFERENCES drivers (session_key, driver_number),
    CHECK (lap_end >= lap_start)
);

CREATE TABLE pit_stops (
    session_key     INTEGER NOT NULL,
    driver_number   INTEGER NOT NULL,
    lap_number      INTEGER NOT NULL,             -- tour d'entrée aux stands
    lane_duration_s REAL CHECK (lane_duration_s > 0),   -- entrée -> sortie de la voie des stands
    stop_duration_s REAL CHECK (stop_duration_s >= 0),  -- voiture immobile (souvent absent)
    PRIMARY KEY (session_key, driver_number, lap_number),
    FOREIGN KEY (session_key, driver_number) REFERENCES drivers (session_key, driver_number)
);

-- Messages de la direction de course (drapeaux, safety car...). Sert au nettoyage.
CREATE TABLE race_control (
    session_key INTEGER NOT NULL REFERENCES sessions (session_key),
    msg_id      INTEGER NOT NULL,                 -- ordre chronologique dans la session
    date        TEXT    NOT NULL,
    lap_number  INTEGER,                          -- tour du leader
    category    TEXT,
    flag        TEXT,
    scope       TEXT,
    sector      INTEGER,                          -- secteur de commissaires, pas de chrono
    message     TEXT    NOT NULL,
    PRIMARY KEY (session_key, msg_id)
);

-- Une ligne par tour et par pilote, enrichie par le nettoyage (cleaning.py).
CREATE TABLE laps (
    session_key    INTEGER NOT NULL,
    driver_number  INTEGER NOT NULL,
    lap_number     INTEGER NOT NULL CHECK (lap_number >= 1),
    date_start     TEXT,
    lap_time_s     REAL CHECK (lap_time_s > 0),
    s1_s           REAL,
    s2_s           REAL,
    s3_s           REAL,
    speed_trap_kmh REAL,
    stint_number   INTEGER,
    compound       TEXT,
    tyre_age       INTEGER CHECK (tyre_age >= 0), -- tours déjà faits par ce train au début du tour
    is_pit_out_lap INTEGER NOT NULL DEFAULT 0 CHECK (is_pit_out_lap IN (0, 1)),
    is_pit_in_lap  INTEGER NOT NULL DEFAULT 0 CHECK (is_pit_in_lap IN (0, 1)),
    track_status   TEXT    NOT NULL DEFAULT 'GREEN'
        CHECK (track_status IN ('GREEN', 'YELLOW', 'VSC', 'SC', 'RED')),
    gap_ahead_s    REAL,                          -- écart à la voiture devant au début du tour
    is_clean       INTEGER NOT NULL DEFAULT 0 CHECK (is_clean IN (0, 1)),
    exclusion      TEXT,                          -- première raison d'exclusion, NULL si propre
    PRIMARY KEY (session_key, driver_number, lap_number),
    FOREIGN KEY (session_key, driver_number) REFERENCES drivers (session_key, driver_number),
    FOREIGN KEY (session_key, driver_number, stint_number)
        REFERENCES stints (session_key, driver_number, stint_number)
);

-- Télémétrie limitée au tour le plus rapide (drapeau vert) de chaque pilote, ~3,7 Hz.
CREATE TABLE telemetry (
    session_key   INTEGER NOT NULL,
    driver_number INTEGER NOT NULL,
    lap_number    INTEGER NOT NULL,
    sample_idx    INTEGER NOT NULL,
    t_s           REAL    NOT NULL CHECK (t_s >= 0),     -- temps depuis le début du tour
    distance_m    REAL    NOT NULL CHECK (distance_m >= 0), -- intégrée depuis la vitesse
    sector        INTEGER NOT NULL CHECK (sector IN (1, 2, 3)),
    speed_kmh     REAL,
    throttle_pct  REAL CHECK (throttle_pct BETWEEN 0 AND 100),
    brake_on      INTEGER CHECK (brake_on IN (0, 1)),
    drs           INTEGER,                        -- code brut ; >= 10 = aileron ouvert
    gear          INTEGER CHECK (gear BETWEEN 0 AND 8),
    rpm           INTEGER,
    PRIMARY KEY (session_key, driver_number, lap_number, sample_idx),
    FOREIGN KEY (session_key, driver_number, lap_number)
        REFERENCES laps (session_key, driver_number, lap_number)
);

-- Index pensés pour les requêtes de sql/queries/ et le modèle.
CREATE INDEX idx_laps_clean_compound ON laps (session_key, is_clean, compound, tyre_age);
CREATE INDEX idx_laps_session_lap    ON laps (session_key, lap_number);
CREATE INDEX idx_stints_compound     ON stints (session_key, compound);
CREATE INDEX idx_telemetry_sector    ON telemetry (session_key, driver_number, sector);
