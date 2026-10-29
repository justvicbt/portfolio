"""Chemins et réglages du projet.

Le code d'ingestion et le modèle de dégradation viennent du projet 1 (paquet f1engine).
Ses chemins par défaut pointent vers le dossier du projet 1 : on les redirige ici vers
data/ du projet 2, pour ne jamais lire ni écrire dans le dossier du projet 1.
"""
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data"
RAW_DIR = DATA_DIR / "raw"            # réponses OpenF1 mises en cache
DB_PATH = DATA_DIR / "f1_2025.db"
DOCS_DIR = ROOT / "docs"
RESULTS_DIR = DOCS_DIR / "results"
SQL_DIR = ROOT / "sql"

# Doit être fixé avant le premier import de matplotlib (y compris via f1engine.plots).
os.environ.setdefault("MPLCONFIGDIR", str(DATA_DIR / ".matplotlib"))

SEASON = 2025
SEED = 2025
N_SIMS = 20_000

# Les quatre circuits du projet 1 : analyse principale.
MAIN_CIRCUITS = ("Sakhir", "Catalunya", "Hungaroring", "Monza")


def get_engine():
    """Moteur SQLite du projet 2, via la fonction du projet 1 (clés étrangères activées)."""
    from f1engine import db
    os.environ["DATABASE_URL"] = f"sqlite:///{DB_PATH}"
    return db.get_engine()
