"""Lectures de la base pour le tableau de bord, sans Streamlit (le cache est dans ui.py, pour les tests)."""
import numpy as np
import pandas as pd
from f1engine.cleaning import neutralisation_windows
from f1engine.config import SQL_DIR as P1_SQL_DIR
from f1engine.degradation import load_clean_laps
from f1engine.db import read_sql
from f1risk.config import SQL_DIR as P2_SQL_DIR


def _dt(s: pd.Series) -> pd.Series:
    return pd.to_datetime(s, utc=True, format="ISO8601")


def sessions(engine) -> pd.DataFrame:
    return read_sql(engine, "SELECT session_key, circuit, country, date_start, total_laps FROM sessions "
                            "ORDER BY date_start")


def race_laps(engine, sk: int) -> pd.DataFrame:
    df = read_sql(engine, """
        SELECT d.acronym AS driver, d.team, l.driver_number, l.lap_number, l.date_start, l.lap_time_s,
               l.stint_number, l.compound, l.tyre_age, l.is_pit_in_lap, l.is_pit_out_lap, l.track_status,
               l.gap_ahead_s, l.is_clean, l.exclusion,
               c.lap_end, c.timing_repaired, c.position, c.gap_to_leader_s, c.air_temp_c, c.track_temp_c, c.humidity_pct,
               c.wind_speed_ms, c.rain, c.weather_status
        FROM laps l
        JOIN drivers d ON d.session_key = l.session_key AND d.driver_number = l.driver_number
        LEFT JOIN lap_conditions c ON c.session_key = l.session_key AND c.driver_number = l.driver_number
                                  AND c.lap_number = l.lap_number
        WHERE l.session_key = :sk
        ORDER BY l.lap_number, c.position""", sk=sk)
    df["date_start"], df["lap_end"] = _dt(df["date_start"]), _dt(df["lap_end"])
    return df


def weather(engine, sk: int) -> pd.DataFrame:
    df = read_sql(engine, "SELECT * FROM weather WHERE session_key = :sk ORDER BY date", sk=sk)
    df["date"] = _dt(df["date"])
    return df


def leader_lap_at(laps: pd.DataFrame, times: pd.Series) -> np.ndarray:
    """Tour du leader en cours à chaque instant (1 + tours déjà bouclés par le leader)."""
    ends = np.sort(laps.loc[laps["position"] == 1, "lap_end"].dropna().to_numpy())
    return np.searchsorted(ends, pd.to_datetime(times, utc=True).to_numpy()) + 1


def neutralisations(engine, sk: int, laps: pd.DataFrame) -> pd.DataFrame:
    """Fenêtres SC, VSC et drapeau rouge (code du moteur de stratégie) en tours du leader, sans les jaunes locaux."""
    rc = read_sql(engine, "SELECT * FROM race_control WHERE session_key = :sk ORDER BY msg_id", sk=sk)
    if rc.empty:
        return pd.DataFrame(columns=["start", "end", "status", "lap_from", "lap_to"])
    rc["date"] = _dt(rc["date"])
    w = neutralisation_windows(rc)
    w = w[w["status"].isin(["SC", "VSC", "RED"])].sort_values("start").reset_index(drop=True)
    w["start"], w["end"] = pd.to_datetime(w["start"], utc=True), pd.to_datetime(w["end"], utc=True)
    w["lap_from"] = leader_lap_at(laps, w["start"])
    w["lap_to"] = leader_lap_at(laps, w["end"])
    return w


def pit_stops(engine, sk: int) -> pd.DataFrame:
    return read_sql(engine, """
        SELECT d.acronym AS driver, p.lap_number, p.lane_duration_s, p.stop_duration_s
        FROM pit_stops p JOIN drivers d ON d.session_key = p.session_key AND d.driver_number = p.driver_number
        WHERE p.session_key = :sk ORDER BY p.lap_number""", sk=sk)


def stints(engine, sk: int) -> pd.DataFrame:
    return read_sql(engine, """
        SELECT d.acronym AS driver, s.stint_number, s.compound, s.lap_start, s.lap_end, s.tyre_age_at_start
        FROM stints s JOIN drivers d ON d.session_key = s.session_key AND d.driver_number = s.driver_number
        WHERE s.session_key = :sk ORDER BY d.acronym, s.stint_number""", sk=sk)


def telemetry(engine, sk: int) -> pd.DataFrame:
    """Télémétrie du tour le plus rapide (drapeau vert) de chaque pilote."""
    return read_sql(engine, """
        SELECT d.acronym AS driver, t.lap_number, t.t_s, t.distance_m, t.speed_kmh, t.throttle_pct, t.brake_on,
               l.lap_time_s, l.compound, l.tyre_age
        FROM telemetry t
        JOIN drivers d ON d.session_key = t.session_key AND d.driver_number = t.driver_number
        JOIN laps l ON l.session_key = t.session_key AND l.driver_number = t.driver_number
                   AND l.lap_number = t.lap_number
        WHERE t.session_key = :sk ORDER BY d.acronym, t.sample_idx""", sk=sk)


def checks(engine, sk: int) -> pd.DataFrame:
    return read_sql(engine, "SELECT check_name, status, value, detail FROM etl_checks WHERE session_key = :sk",
                    sk=sk)


def results(engine, sk: int) -> pd.DataFrame:
    return read_sql(engine, """
        SELECT r.position, d.acronym AS driver, d.team, r.number_of_laps, r.status, r.points
        FROM results r JOIN drivers d ON d.session_key = r.session_key AND d.driver_number = r.driver_number
        WHERE r.session_key = :sk ORDER BY r.position IS NULL, r.position""", sk=sk)


def clean_laps(engine, sk: int) -> pd.DataFrame:
    """Tours propres corrigés du carburant (moteur de stratégie), avec la température de piste du tour."""
    clean = load_clean_laps(engine)
    clean = clean[clean["session_key"] == sk]
    cond = read_sql(engine, """
        SELECT d.acronym AS driver, c.lap_number, c.track_temp_c, c.air_temp_c, c.rain
        FROM lap_conditions c JOIN drivers d ON d.session_key = c.session_key AND d.driver_number = c.driver_number
        WHERE c.session_key = :sk""", sk=sk)
    return clean.reset_index().merge(cond, on=["driver", "lap_number"], how="left").set_index("index")


def pit_losses(engine, circuit: str) -> pd.DataFrame:
    """Perte de chaque arrêt sous drapeau vert (requête du simulateur d'undercut, définition du moteur de stratégie)."""
    df = read_sql(engine, (P2_SQL_DIR / "queries" / "pit_losses.sql").read_text())
    return df[df["circuit"] == circuit]


def pit_loss_summary(engine) -> pd.DataFrame:
    """Médiane par course (requête 04 du moteur de stratégie)."""
    return read_sql(engine, (P1_SQL_DIR / "queries" / "04_pit_loss.sql").read_text())
