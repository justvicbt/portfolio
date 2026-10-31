from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
DOCS_DIR = ROOT / "docs"
RESULTS_DIR = DOCS_DIR / "results"


@dataclass(frozen=True)
class Seuils:
    fond_pct: float = 98.0           # petite marge sous 100 % ; à Monza 2025, 98 et 100 donnent le même résultat
    rapide_ratio: float = 0.90       # relatif à la vitesse max du tour, pour rester valable sur tout circuit
    rapide_duree_s: float = 2.0      # écarte les mesures isolées au-dessus du seuil
    freinage_mesures: int = 2        # au moins 2 mesures de frein (~0,5 s à ~4 Hz)
    freinage_baisse_kmh: float = 30.0  # écarte les simples touches de frein
    trou_max_s: float = 1.0          # au-delà, pas d'interpolation entre deux mesures
