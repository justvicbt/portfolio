"""Chemins et réglages du projet.

Le code d'ingestion, de nettoyage, de dégradation (projet 1, paquet f1engine) et le
simulateur d'undercut (projet 2, paquet f1risk) sont réutilisés tels quels. Leurs chemins
par défaut pointent vers leurs propres dossiers : on les redirige ici vers data/ du
projet 3, pour ne jamais lire ni écrire dans les dossiers de données des projets 1 et 2.
"""
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data"
RAW_DIR = DATA_DIR / "raw"            # réponses OpenF1 mises en cache
DEFAULT_DB = DATA_DIR / "f1cc.db"      # F1CC_DB permet d'en choisir une autre (tests)
SQL_DIR = ROOT / "sql"

# À fixer avant tout import de f1engine / f1risk :
# - f1risk.config place MPLCONFIGDIR dans le projet 2 s'il n'est pas déjà défini ;
# - f1engine.config lit DATABASE_URL (sinon la base du projet 1).
os.environ["MPLCONFIGDIR"] = str(DATA_DIR / ".matplotlib")
os.environ["DATABASE_URL"] = f"sqlite:///{DEFAULT_DB}"

# Résultats versionnés du projet 2 (paramètres de saison estimés sur 24 courses), lus seulement.
P2_RESULTS = ROOT.parent / "f1-risk-simulator" / "docs" / "results"

SEASON = 2025
SEED = 2025


def circuits() -> list[str]:
    raw = os.getenv("F1CC_CIRCUITS", "Sakhir,Hungaroring,Monza,Silverstone")
    return [c.strip() for c in raw.split(",") if c.strip()]


CIRCUIT_LABEL = {"Sakhir": "Bahreïn (Sakhir)", "Hungaroring": "Hongrie (Hungaroring)",
                 "Monza": "Italie (Monza)", "Silverstone": "Grande-Bretagne (Silverstone)"}

# Alignement météo / tours
WEATHER_TOLERANCE_S = 90     # mesure la plus proche du milieu du tour, au plus à 90 s
WEATHER_MAX_GAP_S = 300      # au-delà de 5 min sans mesure, on n'interpole pas

# Seuils de suffisance des données (les deux premiers viennent du projet 1)
MIN_LAPS = 30                # tours propres par composé
MIN_STINTS = 3               # relais par composé
MIN_STINT_LAPS = 8           # tours propres pour une pente par relais
MIN_PIT_STOPS = 5            # arrêts mesurés (même seuil que la validation du projet 2)
MAX_UNDERCUT_GAP_S = 3.0     # domaine de validation du simulateur du projet 2


def db_path() -> Path:
    return Path(os.getenv("F1CC_DB", DEFAULT_DB))


def get_engine():
    """Moteur SQLite du projet 3, via la fonction du projet 1 (clés étrangères activées)."""
    from f1engine import db
    os.environ["DATABASE_URL"] = f"sqlite:///{db_path()}"
    return db.get_engine()
