"""Courses construites à la main, où la vraie dégradation est connue."""
import numpy as np
import pandas as pd

from f1pneus.config import Carburant
from f1pneus.nettoyage import carburant_kg

T0 = pd.Timestamp("2025-08-03T13:00:00Z")


def tours(lignes: list[dict]) -> pd.DataFrame:
    """Tours minimaux ; les colonnes absentes prennent une valeur neutre (piste verte, air libre, sec)."""
    df = pd.DataFrame(lignes)
    defauts = {"pilote": "AAA", "numero": 1, "duree": 80.0, "sortie_stands": False, "entree_stands": False,
               "relais": 1, "gomme": "MEDIUM", "age_pneus": 5, "neutralisation": "", "pluie": False,
               "ecart_phys_debut": 5.0, "ecart_phys_fin": 5.0, "ecart_openf1_debut": 5.0,
               "ecart_openf1_fin": 5.0, "devant": "même tour"}
    for k, v in defauts.items():
        if k not in df:
            df[k] = v
    if "debut" not in df:
        df["debut"] = T0 + pd.to_timedelta((df["tour"] - 1) * 80.0, unit="s")
    df["fin"] = df["debut"] + pd.to_timedelta(df["duree"].fillna(80.0), unit="s")
    df["relais"] = df["relais"].astype("Int64")
    df["age_pneus"] = df["age_pneus"].astype("Int64")
    return df


def course_simulee(graine=1, n_pilotes=14, total=60, pentes=None, niveaux=None, bruit=0.25, cout_trafic=0.8,
                   p_trafic=0.6, carb=Carburant(), perte_arret=20.0):
    """Peloton à 1 ou 2 arrêts (medium puis dur), avec carburant, bruit et trafic en début de relais.

    Le trafic tombe surtout dans les premiers tours de chaque relais, comme en course quand on ressort dans le
    peloton : s'il n'est pas retiré, il fait paraître les pneus neufs plus lents et écrase la pente.
    """
    pentes = pentes or {"MEDIUM": 0.08, "HARD": 0.04}
    niveaux = niveaux or {"MEDIUM": 0.0, "HARD": 0.4}
    rng = np.random.default_rng(graine)
    lignes = []
    for i in range(n_pilotes):
        pilote, rythme = f"P{i:02d}", rng.normal(0, 0.3)
        arrets = [int(rng.integers(20, 35))] if i % 2 == 0 else sorted(rng.choice(range(15, 46), 2, replace=False))
        bornes = [1] + [a + 1 for a in arrets] + [total + 1]
        for r in range(len(bornes) - 1):
            gomme = "MEDIUM" if r == 0 else "HARD"
            for tour in range(bornes[r], bornes[r + 1]):
                age = tour - bornes[r]
                trafic = age < 6 and rng.random() < p_trafic
                temps = (80 + rythme + niveaux[gomme] + pentes[gomme] * age
                         + carb.s_par_kg * carburant_kg(tour, total, carb)[()] + rng.normal(0, bruit)
                         + cout_trafic * trafic)
                entree, sortie = tour in arrets, r > 0 and tour == bornes[r]
                temps += perte_arret * 0.15 * entree + perte_arret * 0.85 * sortie + 5.0 * (tour == 1)
                lignes.append({"pilote": pilote, "numero": i + 1, "tour": tour, "duree": temps, "relais": r + 1,
                               "gomme": gomme, "age_pneus": age, "entree_stands": entree, "sortie_stands": sortie,
                               "ecart_phys_debut": 0.8 if trafic else 4.0, "ecart_phys_fin": 0.8 if trafic else 4.0})
    df = tours(lignes)
    df["debut"] = T0 + pd.to_timedelta(df.groupby("pilote")["duree"].cumsum() - df["duree"], unit="s")
    df["fin"] = df["debut"] + pd.to_timedelta(df["duree"], unit="s")
    return df, {"pentes": pentes, "niveaux": niveaux, "perte_arret": perte_arret}
