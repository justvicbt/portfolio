"""Configuration lue depuis l'environnement (fichier .env facultatif)."""
import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / ".env")

DATA_DIR = ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
DOCS_DIR = ROOT / "docs"
RESULTS_DIR = DOCS_DIR / "results"
SQL_DIR = ROOT / "sql"

DRY_COMPOUNDS = ("SOFT", "MEDIUM", "HARD")


@dataclass(frozen=True)
class FuelModel:
    """Hypothèse simple : la voiture brûle son carburant à débit constant."""
    start_kg: float = 100.0
    sec_per_kg: float = 0.03


@dataclass(frozen=True)
class CleaningRules:
    min_gap_ahead_s: float = 1.5     # en dessous : tour considéré "dans le trafic"
    outlier_ratio: float = 1.07      # > 107 % de la médiane du pilote : tour aberrant
    sc_buffer_s: float = 30.0        # prolongation des fenêtres SC / VSC (tour de relance)
    yellow_fallback_s: float = 60.0  # durée par défaut d'un jaune sans "CLEAR"


def database_url() -> str:
    url = os.getenv("DATABASE_URL", "sqlite:///data/f1.db")
    # Rend le chemin SQLite relatif à la racine du projet, quel que soit le dossier courant.
    if url.startswith("sqlite:///") and not url.startswith("sqlite:////"):
        url = f"sqlite:///{ROOT / url.removeprefix('sqlite:///')}"
    return url


def season() -> int:
    return int(os.getenv("F1_SEASON", "2025"))


def circuits() -> list[str]:
    raw = os.getenv("F1_CIRCUITS", "Sakhir,Catalunya,Hungaroring,Monza")
    return [c.strip() for c in raw.split(",") if c.strip()]


def fuel_model() -> FuelModel:
    return FuelModel(
        start_kg=float(os.getenv("FUEL_START_KG", "100")),
        sec_per_kg=float(os.getenv("FUEL_SEC_PER_KG", "0.03")),
    )
