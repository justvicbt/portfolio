"""Chemins et réglages ; ceux de f1engine et f1risk sont redirigés vers data/ de ce projet."""
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
DEFAULT_DB = DATA_DIR / "f1cc.db"      # F1CC_DB permet d'en choisir une autre (tests)
SQL_DIR = ROOT / "sql"

# Avant f1engine et f1risk : sinon MPLCONFIGDIR et DATABASE_URL pointeraient vers leurs propres dossiers.
os.environ["MPLCONFIGDIR"] = str(DATA_DIR / ".matplotlib")
os.environ["DATABASE_URL"] = f"sqlite:///{DEFAULT_DB}"

# Résultats versionnés du projet Risque d'undercut F1 (paramètres de saison estimés sur 24 courses), lus seulement.
P2_RESULTS = ROOT.parent / "risque-undercut-f1" / "docs" / "results"

SEASON = 2025
SEED = 2025


def circuits() -> list[str]:
    raw = os.getenv("F1CC_CIRCUITS", "Sakhir,Hungaroring,Monza,Silverstone")
    return [c.strip() for c in raw.split(",") if c.strip()]


CIRCUIT_LABEL = {"Sakhir": "Bahreïn (Sakhir)", "Hungaroring": "Hongrie (Hungaroring)",
                 "Monza": "Italie (Monza)", "Silverstone": "Grande-Bretagne (Silverstone)"}

WEATHER_TOLERANCE_S = 90     # mesure la plus proche du milieu du tour, au plus à 90 s
WEATHER_MAX_GAP_S = 300      # au-delà de 5 min sans mesure, on n'interpole pas

# Seuils de suffisance des données (les deux premiers viennent du moteur de stratégie)
MIN_LAPS = 30                # tours propres par composé
MIN_STINTS = 3               # relais par composé
MIN_STINT_LAPS = 8           # tours propres pour une pente par relais
MIN_PIT_STOPS = 5            # arrêts mesurés (même seuil que la validation du simulateur d'undercut)
MAX_UNDERCUT_GAP_S = 3.0     # domaine de validation du simulateur d'undercut


def db_path() -> Path:
    return Path(os.getenv("F1CC_DB", DEFAULT_DB))


def get_engine():
    """Moteur SQLite de ce projet, via la fonction du moteur de stratégie (clés étrangères activées)."""
    from f1engine import db
    os.environ["DATABASE_URL"] = f"sqlite:///{db_path()}"
    return db.get_engine()
