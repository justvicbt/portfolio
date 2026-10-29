"""Pipeline ETL : OpenF1 -> transformation -> SQLite (data/f1cc.db).

1. Extraction et chargement des tables du projet 1 avec son code (f1engine.ingest.ingest_race) :
   tours, relais, arrêts, direction de course, pilotes, télémétrie du tour le plus rapide de
   chaque pilote. Le nettoyage du projet 1 (SC/VSC, trafic, aberrants) est appliqué au passage.
2. Extraction de la météo et du classement officiel (endpoints weather et session_result).
3. Transformation propre au projet 3 : validation de la météo, alignement sur les tours,
   positions et écarts au leader recalculés, contrôles de cohérence.
4. Chargement dans weather, results, lap_conditions et etl_checks (sql/schema_cc.sql).

La base est reconstruite à chaque lancement. Les réponses OpenF1 sont gardées dans data/raw/
du projet 3 : un second lancement ne retélécharge rien.
"""
from contextlib import contextmanager

import pandas as pd
from f1engine import ingest as p1_ingest
from f1engine import openf1
from f1engine.db import create_schema, read_sql, split_statements
from f1risk.ingest import valid_stint
from sqlalchemy import text

from . import transform
from .config import RAW_DIR, SEASON, SQL_DIR, circuits, get_engine
from .text import plural


def _iso(series: pd.Series) -> pd.Series:
    return series.dt.strftime("%Y-%m-%dT%H:%M:%S.%fZ")


@contextmanager
def project3_openf1():
    """Cache OpenF1 dans le projet 3 ; relais incohérents retirés (même filtre que le projet 2)."""
    original_get, original_dir = openf1.get, openf1.RAW_DIR

    def patched_get(endpoint, **params):
        data = original_get(endpoint, **params)
        if endpoint == "stints":
            data = [s for s in data if valid_stint(s)]
        return data

    openf1.RAW_DIR, openf1.get = RAW_DIR, patched_get
    try:
        yield
    finally:
        openf1.RAW_DIR, openf1.get = original_dir, original_get


def create_all_tables(engine) -> None:
    # Tables du projet 3 d'abord (voir l'en-tête de schema_cc.sql), puis celles du projet 1.
    with engine.begin() as conn:
        for stmt in split_statements((SQL_DIR / "schema_cc.sql").read_text()):
            conn.execute(text(stmt))
    create_schema(engine)


def load_laps(engine, session_key: int) -> pd.DataFrame:
    laps = read_sql(engine, """
        SELECT driver_number, lap_number, date_start, lap_time_s, is_clean
        FROM laps WHERE session_key = :sk""", sk=session_key)
    laps["date_start"] = pd.to_datetime(laps["date_start"], utc=True, format="ISO8601")
    return laps


def build_conditions(laps: pd.DataFrame, weather: pd.DataFrame) -> pd.DataFrame:
    """Une ligne par tour : fin de tour, position, écart au leader, conditions météo."""
    laps = laps.copy()
    # Heures de passage : on corrige les débuts de tour isolément faux avant de calculer
    # les fins de tour, les positions et les écarts (la table laps du projet 1 reste brute).
    repaired = transform.repair_date_starts(laps)
    laps["timing_repaired"] = (repaired != laps["date_start"]).astype(int)
    laps["date_start"] = repaired
    laps["lap_end"] = transform.lap_end_times(laps)
    pos = transform.positions_and_gaps(laps)
    cond = transform.align_weather(laps, weather)
    out = pd.concat([laps[["driver_number", "lap_number", "lap_end", "timing_repaired"]], pos, cond], axis=1)
    out["position"] = out["position"].astype("Int64")
    return out


def transform_and_load(engine, session_key: int, raw_weather: list[dict], raw_results: list[dict]) -> dict:
    """Étapes 3 et 4 pour une course déjà chargée par le code du projet 1."""
    known = set(read_sql(engine, "SELECT driver_number FROM drivers WHERE session_key = :sk",
                         sk=session_key)["driver_number"])
    weather, rejected = transform.validate_weather(pd.DataFrame(raw_weather, columns=[
        "date", "air_temperature", "track_temperature", "humidity", "pressure", "wind_speed",
        "wind_direction", "rainfall"]))
    results = transform.results_table(raw_results, known)
    laps = load_laps(engine, session_key)
    cond = build_conditions(laps, weather)
    checks = transform.consistency_checks(laps.assign(lap_end=cond["lap_end"]), cond, results, rejected)
    n_rep = int(cond["timing_repaired"].sum())
    checks.append({"check_name": "lap_start_repaired", "status": "ok" if n_rep == 0 else "warning", "value": n_rep,
                   "detail": f"{plural(n_rep, 'heure de début de tour incohérente', 'heures de début de tour incohérentes')}"
                             f" avec les tours voisins, {'corrigées' if n_rep > 1 else 'corrigée'} à partir du tour précédent"})

    with engine.begin() as conn:
        weather.assign(session_key=session_key, date=_iso(weather["date"])).to_sql(
            "weather", conn, if_exists="append", index=False)
        results.assign(session_key=session_key).to_sql("results", conn, if_exists="append", index=False)
        cond.assign(session_key=session_key, lap_end=_iso(cond["lap_end"])).to_sql(
            "lap_conditions", conn, if_exists="append", index=False)
        pd.DataFrame(checks).assign(session_key=session_key).to_sql("etl_checks", conn, if_exists="append",
                                                                    index=False)
    return {"weather_samples": len(weather), "weather_rejected": rejected,
            "checks_not_ok": sum(c["status"] != "ok" for c in checks)}


def main() -> None:
    engine = get_engine()
    create_all_tables(engine)
    skipped = []
    with project3_openf1():
        for circuit in circuits():
            print(f"Chargement {circuit} {SEASON}...", flush=True)
            try:
                stats = p1_ingest.ingest_race(engine, SEASON, circuit)
                sk = stats["session_key"]
                stats |= transform_and_load(engine, sk, openf1.get("weather", session_key=sk),
                                            openf1.get("session_result", session_key=sk))
                print("  " + ", ".join(f"{k}={v}" for k, v in stats.items()), flush=True)
            except Exception as exc:   # course incomplète : on garde la trace et on continue
                skipped.append(circuit)
                print(f"  ignorée : {type(exc).__name__}: {str(exc).splitlines()[0]}", flush=True)
    checks = read_sql(engine, """
        SELECT s.circuit, c.check_name, c.status, c.detail FROM etl_checks c JOIN sessions s USING (session_key)
        WHERE c.status != 'ok' ORDER BY s.circuit""")
    if len(checks):
        print("\nContrôles à regarder :")
        print(checks.to_string(index=False))
    if skipped:
        print("Courses ignorées :", ", ".join(skipped))
