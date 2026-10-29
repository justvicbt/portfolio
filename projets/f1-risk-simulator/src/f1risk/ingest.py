"""Ingestion de toutes les courses de la saison, avec le code du projet 1.

On appelle f1engine.ingest.ingest_race tel quel, avec trois réglages :
- le cache OpenF1 est redirigé vers data/raw/ du projet 2 ;
- la télémétrie n'est pas téléchargée (inutile ici, et 20 requêtes par course) ;
- les relais incohérents (fin avant le début) sont retirés avant l'insertion. Il y en a
  quelques-uns à Melbourne et à Monaco ; sans ce filtre, le schéma rejette toute la course.
"""
from contextlib import contextmanager

from f1engine import ingest as p1_ingest
from f1engine import openf1
from f1engine.db import create_schema

from .config import RAW_DIR, SEASON, get_engine

dropped_stints: list[dict] = []


def valid_stint(stint: dict) -> bool:
    start, end = stint.get("lap_start"), stint.get("lap_end")
    return start is None or end is None or end >= start


@contextmanager
def project2_openf1():
    """Cache dans le projet 2, pas de télémétrie, relais incohérents retirés."""
    original_get, original_dir = openf1.get, openf1.RAW_DIR

    def patched_get(endpoint, **params):
        if endpoint == "car_data":
            return []
        data = original_get(endpoint, **params)
        if endpoint == "stints":
            dropped_stints.extend(s for s in data if not valid_stint(s))
            data = [s for s in data if valid_stint(s)]
        return data

    openf1.RAW_DIR, openf1.get = RAW_DIR, patched_get
    try:
        yield
    finally:
        openf1.RAW_DIR, openf1.get = original_dir, original_get


def season_circuits(year: int = SEASON) -> list[str]:
    races = openf1.get("sessions", year=year, session_name="Race")
    return [r["circuit_short_name"] for r in sorted(races, key=lambda r: r["date_start"])]


def main() -> None:
    engine = get_engine()
    create_schema(engine)   # schéma du projet 1 (la table telemetry reste vide)
    skipped = []
    with project2_openf1():
        circuits = season_circuits()
        print(f"{len(circuits)} courses en {SEASON}", flush=True)
        for circuit in circuits:
            print(f"Chargement {circuit}...", flush=True)
            n_dropped = len(dropped_stints)
            try:
                stats = p1_ingest.ingest_race(engine, SEASON, circuit)
                print("  " + ", ".join(f"{k}={v}" for k, v in stats.items()), flush=True)
            except Exception as exc:   # données incomplètes : on garde la trace et on continue
                skipped.append(circuit)
                print(f"  ignorée : {type(exc).__name__}: {str(exc).splitlines()[0]}", flush=True)
            if len(dropped_stints) > n_dropped:
                print(f"  {len(dropped_stints) - n_dropped} relais incohérents retirés", flush=True)
    if skipped:
        print("Courses ignorées :", ", ".join(skipped))
