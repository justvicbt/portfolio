"""Chemins et réglages ; ceux du moteur de stratégie (f1engine) sont redirigés vers data/ de ce projet."""
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
DB_PATH = DATA_DIR / "f1_2025.db"
DOCS_DIR = ROOT / "docs"
RESULTS_DIR = DOCS_DIR / "results"
SQL_DIR = ROOT / "sql"

# Doit être fixé avant le premier import de matplotlib (y compris via f1engine.plots).
os.environ.setdefault("MPLCONFIGDIR", str(DATA_DIR / ".matplotlib"))

SEASON = 2025
SEED = 2025
N_SIMS = 20_000

# Les quatre circuits du moteur de stratégie : analyse principale.
MAIN_CIRCUITS = ("Sakhir", "Catalunya", "Hungaroring", "Monza")


def get_engine():
    """Moteur SQLite de ce projet, via la fonction du moteur de stratégie (clés étrangères activées)."""
    from f1engine import db
    os.environ["DATABASE_URL"] = f"sqlite:///{DB_PATH}"
    return db.get_engine()
