from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
DOCS_DIR = ROOT / "docs"
RESULTS_DIR = DOCS_DIR / "results"

GOMMES_SECHES = ("SOFT", "MEDIUM", "HARD")
NOMS_GOMMES = {"SOFT": "tendre", "MEDIUM": "medium", "HARD": "dur"}


@dataclass(frozen=True)
class Seuils:
    air_libre_s: float = 1.5          # écart sur la ligne en dessous duquel le tour compte comme « dans le trafic »
    source_ecart: str = "physique"     # "physique" (voiture devant sur la piste) ou "openf1" (voiture devant au classement)
    aberrant_s: float | None = 1.0     # écart à la médiane glissante du relais ; None : pas de filtre
    fenetre_aberrant: int = 7          # tours ; une médiane sur tout le relais rejetterait les tours usés de fin de relais
    marge_neutralisation_s: float = 30.0   # tour de relance après SC ou VSC
    jaune_par_defaut_s: float = 60.0   # durée d'un jaune jamais refermé dans les messages
    retirer_jaunes: bool = True
    retirer_annules: bool = True
    min_tours_relais: int = 8          # pente d'un relais affichée seulement à partir de ce nombre de tours propres
    min_relais_gomme: int = 3          # pente d'une gomme estimée seulement avec ce nombre de relais...
    min_pilotes_gomme: int = 2         # ... venant d'au moins ce nombre de pilotes


@dataclass(frozen=True)
class Carburant:
    # 100 kg au départ (maximum réglementaire 110 kg, les équipes partent rarement pleines) et 0,03 s par kg,
    # l'ordre de grandeur cité par les équipes et Pirelli ; les deux valeurs sont testées en sensibilité.
    depart_kg: float = 100.0
    s_par_kg: float = 0.03


SCENARIOS_CARBURANT = (0.02, 0.03, 0.04)
