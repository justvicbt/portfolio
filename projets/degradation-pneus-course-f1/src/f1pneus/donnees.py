import pandas as pd

from . import openf1
from .config import Seuils
from .nettoyage import (ajouter_meteo, construire_tours, ecart_openf1, ecart_physique, etat_piste,
                        fenetres_neutralisation, marquer, tours_annules)

ENDPOINTS = ("drivers", "laps", "stints", "pit", "race_control", "intervals", "weather", "session_result")


def session_course(annee: int, circuit: str) -> dict:
    sessions = openf1.get("sessions", year=annee, circuit_short_name=circuit, session_name="Race")
    if not sessions:
        raise ValueError(f"Aucune course trouvée pour {circuit} {annee} (nom court OpenF1 attendu).")
    return sessions[0]


def telecharger(annee: int, circuit: str) -> dict:
    session = session_course(annee, circuit)
    brut = {"session": session}
    for ep in ENDPOINTS:
        brut[ep] = openf1.get(ep, session_key=session["session_key"])
    return brut


def tours_de_base(brut: dict) -> pd.DataFrame:
    """Tours avec pneus, écarts, météo et état de la piste, avant les filtres (qui dépendent des seuils)."""
    df = construire_tours(brut["laps"], brut["stints"], brut["pit"], brut["drivers"])
    df = ecart_physique(df)
    df = ecart_openf1(df, brut["intervals"])
    df = ajouter_meteo(df, brut["weather"])
    return df


def preparer(brut: dict, base: pd.DataFrame, seuils: Seuils) -> pd.DataFrame:
    df = base.copy()
    df["neutralisation"] = etat_piste(df, fenetres_neutralisation(brut["race_control"], seuils))
    return marquer(df, tours_annules(brut["race_control"], df), seuils)


def nombre_de_tours(brut: dict) -> int:
    res = [r for r in brut["session_result"] if r.get("position") == 1]
    if res and res[0].get("number_of_laps"):
        return int(res[0]["number_of_laps"])
    return int(max(l["lap_number"] for l in brut["laps"]))
