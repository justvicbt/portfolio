"""Base de test construite à la main : une course fictive de 30 tours, 6 pilotes, sans réseau.

Elle passe par le vrai code : nettoyage du projet 1 (fenêtres de neutralisation, tours propres)
puis transformation et chargement du projet 3 (etl.transform_and_load). Elle est écrite dans
data/test/ (ignoré par git), pas dans un dossier temporaire du système.
"""
import numpy as np
import pandas as pd
import pytest
from f1engine.cleaning import assign_track_status, mark_clean, neutralisation_windows

from f1cc import etl
from f1cc.config import DATA_DIR

T0 = pd.Timestamp("2025-06-01T13:00:00Z")
N_LAPS, PIT_LAP = 30, 15
DRIVERS = {1: "AAA", 2: "BBB", 3: "CCC", 4: "DDD", 5: "EEE", 6: "FFF"}
VSC = (T0 + pd.Timedelta(minutes=30), T0 + pd.Timedelta(minutes=32))


def iso(t: pd.Timestamp) -> str:
    return t.strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def synthetic_race():
    rng = np.random.default_rng(0)
    rows = []
    for i, num in enumerate(DRIVERS):
        t = T0 + pd.Timedelta(seconds=0.5 * i)   # écart sur la grille
        for n in range(1, N_LAPS + 1):
            compound, age = ("MEDIUM", n - 1) if n <= PIT_LAP else ("HARD", n - PIT_LAP - 1)
            slope = 0.05 if compound == "MEDIUM" else 0.03
            lap = 90 + 0.2 * i + slope * age + 0.03 * 100 * (1 - (n - 0.5) / N_LAPS) + rng.normal(0, 0.1)
            lap += 10 if n == PIT_LAP else 12 if n == PIT_LAP + 1 else 0
            lap += 5 if n == 1 else 0
            rows.append({"driver_number": num, "lap_number": n, "date_start": t, "lap_time_s": lap,
                         "stint_number": 1 if n <= PIT_LAP else 2, "compound": compound, "tyre_age": age,
                         "is_pit_in_lap": int(n == PIT_LAP), "is_pit_out_lap": int(n == PIT_LAP + 1),
                         "gap_ahead_s": np.nan})
            t += pd.Timedelta(seconds=lap)
    laps = pd.DataFrame(rows)
    rc = pd.DataFrame([
        {"date": VSC[0], "lap_number": 20, "category": "SafetyCar", "flag": None, "scope": None, "sector": None,
         "message": "VIRTUAL SAFETY CAR DEPLOYED"},
        {"date": VSC[1], "lap_number": 21, "category": "SafetyCar", "flag": None, "scope": None, "sector": None,
         "message": "VIRTUAL SAFETY CAR ENDING"},
    ])
    laps["track_status"] = assign_track_status(laps, neutralisation_windows(rc))
    laps = mark_clean(laps)
    return laps, rc


def synthetic_weather(end: pd.Timestamp) -> list[dict]:
    """Une mesure par minute, piste de 30 à 38 °C, et un trou de 6 minutes (tours sans météo)."""
    out, t, k = [], T0 - pd.Timedelta(minutes=2), 0
    while t <= end + pd.Timedelta(minutes=2):
        if not (T0 + pd.Timedelta(minutes=10) < t < T0 + pd.Timedelta(minutes=16)):
            out.append({"date": iso(t), "air_temperature": 24.0, "track_temperature": 30 + 8 * k / 50,
                        "humidity": 50.0, "pressure": 1010.0, "wind_speed": 2.0, "wind_direction": 180,
                        "rainfall": 0})
        t += pd.Timedelta(minutes=1)
        k += 1
    return out


def build_db(path):
    from f1cc.config import get_engine
    engine = get_engine()
    etl.create_all_tables(engine)
    laps, rc = synthetic_race()
    total = laps.groupby("driver_number")["lap_time_s"].sum().sort_values()
    with engine.begin() as conn:
        pd.DataFrame([{"session_key": 1, "meeting_key": 1, "year": 2025, "circuit": "Testring", "country": "Test",
                       "date_start": iso(T0), "total_laps": N_LAPS}]).to_sql("sessions", conn, if_exists="append",
                                                                                index=False)
        pd.DataFrame([{"session_key": 1, "driver_number": k, "acronym": v, "full_name": v, "team": "Équipe test"}
                      for k, v in DRIVERS.items()]).to_sql("drivers", conn, if_exists="append", index=False)
        pd.DataFrame([{"session_key": 1, "driver_number": k, "stint_number": s, "compound": c, "lap_start": a,
                       "lap_end": b, "tyre_age_at_start": 0}
                      for k in DRIVERS for s, c, a, b in ((1, "MEDIUM", 1, PIT_LAP), (2, "HARD", PIT_LAP + 1, N_LAPS))]
                     ).to_sql("stints", conn, if_exists="append", index=False)
        pd.DataFrame([{"session_key": 1, "driver_number": k, "lap_number": PIT_LAP, "lane_duration_s": 21.0,
                       "stop_duration_s": 2.5} for k in DRIVERS]).to_sql("pit_stops", conn, if_exists="append",
                                                                         index=False)
        rc.assign(session_key=1, msg_id=rc.index, date=rc["date"].map(iso)).to_sql(
            "race_control", conn, if_exists="append", index=False)
        laps.assign(session_key=1, date_start=laps["date_start"].map(iso), s1_s=30.0, s2_s=30.0, s3_s=30.0,
                    speed_trap_kmh=300.0)[[
            "session_key", "driver_number", "lap_number", "date_start", "lap_time_s", "s1_s", "s2_s", "s3_s",
            "speed_trap_kmh", "stint_number", "compound", "tyre_age", "is_pit_out_lap", "is_pit_in_lap",
            "track_status", "gap_ahead_s", "is_clean", "exclusion"]].to_sql("laps", conn, if_exists="append",
                                                                             index=False)
        # Télémétrie : tour 10 de chaque pilote, vitesse constante (le plus lent finit plus loin en temps).
        tel = []
        for i, k in enumerate(DRIVERS):
            lap_time = float(laps.loc[(laps["driver_number"] == k) & (laps["lap_number"] == 10), "lap_time_s"].iloc[0])
            for j, ts in enumerate(np.linspace(0, lap_time, 60)):
                tel.append({"session_key": 1, "driver_number": k, "lap_number": 10, "sample_idx": j, "t_s": ts,
                            "distance_m": 5000 * ts / lap_time, "sector": 1 + min(int(ts // 30), 2),
                            "speed_kmh": 200.0, "throttle_pct": 100.0, "brake_on": 0, "drs": 0, "gear": 7,
                            "rpm": 11000})
        pd.DataFrame(tel).to_sql("telemetry", conn, if_exists="append", index=False)
    end = laps["date_start"].max() + pd.Timedelta(seconds=100)
    results = [{"driver_number": k, "position": p + 1, "number_of_laps": N_LAPS, "points": 0.0, "dnf": False,
                "dns": False, "dsq": False} for p, k in enumerate(total.index)]
    etl.transform_and_load(engine, 1, synthetic_weather(end), results)


@pytest.fixture(scope="session")
def synthetic_db():
    import os
    path = DATA_DIR / "test" / "synthetic.db"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.unlink(missing_ok=True)
    previous = os.environ.get("F1CC_DB")
    os.environ["F1CC_DB"] = str(path)
    try:
        build_db(path)
    finally:
        if previous is None:
            os.environ.pop("F1CC_DB")
        else:
            os.environ["F1CC_DB"] = previous
    return path
