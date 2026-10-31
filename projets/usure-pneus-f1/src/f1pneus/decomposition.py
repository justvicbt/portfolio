import numpy as np
import pandas as pd

from .config import Carburant, Seuils
from .modele import ModeleNiveaux, ajuster_niveaux, preparer_regression
from .nettoyage import carburant_kg

COMPOSANTES = ("arrêts", "niveau de la gomme", "usure des pneus", "trafic", "pilotage et non expliqué",
               "départ et tour 1")
STRATEGIE = ("arrêts", "niveau de la gomme", "usure des pneus")


def ecart_final(resultats: list[dict], df: pd.DataFrame, a: str, b: str) -> float:
    """Écart final de b sur a (positif : b derrière), d'après le classement officiel, sinon les passages sur la ligne."""
    num = df.drop_duplicates("pilote").set_index("pilote")["numero"]
    res = {r["driver_number"]: r for r in resultats}
    duree = [res.get(num[p], {}).get("duration") for p in (a, b)]
    if all(isinstance(x, (int, float)) for x in duree):
        return float(duree[1] - duree[0])
    fins = df.sort_values("tour").groupby("pilote")["fin"].last()
    return (fins[b] - fins[a]).total_seconds()


def tours_du_pilote(df: pd.DataFrame, pilote: str, total_tours: int, carb: Carburant) -> pd.DataFrame:
    x = df[df["pilote"] == pilote].sort_values("tour").copy()
    if len(x) != total_tours or x["duree"].iloc[1:].isna().any():
        raise ValueError(f"{pilote} n'a pas tous ses temps au tour : la décomposition demande deux courses complètes.")
    x["carburant_s"] = carb.s_par_kg * carburant_kg(x["tour"], total_tours, carb)
    x["nature"] = np.where(x["tour"] == 1, "départ",
                           np.where(x["entree_stands"] | x["sortie_stands"], "arrêt", "normal"))
    # Le trafic d'un tour d'entrée ou de sortie est compté dans la perte de l'arrêt.
    x["duel"] = x["trafic"] & (x["devant"] != "retardataire") & (x["nature"] == "normal")
    x["retard"] = x["trafic"] & (x["devant"] == "retardataire") & (x["nature"] == "normal")
    x["id_relais"] = x["pilote"] + "-" + x["relais"].astype(str)
    return x


def composantes_pilote(x: pd.DataFrame, m: ModeleNiveaux) -> dict:
    p = m.p
    x = x[x["tour"] >= 2]
    if not x["gomme"].isin(m.gommes).all():
        raise ValueError("une gomme du pilote n'a pas de pente estimable")
    if m.variante in ("pilote", "tendance"):
        gomme = x["gomme"].map(lambda c: p.get(f"gomme:{c}", 0.0)).to_numpy()
        autre = np.full(len(x), p[f"pilote:{x['pilote'].iloc[0]}"])
    else:
        # Le niveau d'un relais mélange pilote, gomme et état de la piste : il ne se sépare pas.
        gomme = np.zeros(len(x))
        autre = x["id_relais"].map(lambda r: p[f"relais:{r}"]).to_numpy()
    usure = x["gomme"].map(lambda c: p[f"pente:{c}"]).to_numpy() * x["age_pneus"].to_numpy(float)
    trafic = (p.get("trafic_duel", 0.0) * x["duel"].to_numpy(float)
              + p.get("trafic_retard", 0.0) * x["retard"].to_numpy(float))
    # La tendance est la même pour les deux pilotes sur un même tour : comme le carburant, elle s'annule.
    tendance = p.get("tendance", 0.0) * x["tour"].to_numpy(float)
    ecart = x["duree"].to_numpy() - x["carburant_s"].to_numpy() - tendance - (autre + gomme + usure + trafic)
    arret = (x["nature"] == "arrêt").to_numpy()
    return {"arrêts": ecart[arret].sum(), "niveau de la gomme": gomme.sum(), "usure des pneus": usure.sum(),
            "trafic": trafic.sum(), "pilotage et non expliqué": autre.sum() + ecart[~arret].sum(),
            "temps": x["duree"].sum(), "pertes": pd.Series(ecart[arret], index=x.loc[arret, "tour"].to_numpy())}


def difference(xa, xb, m: ModeleNiveaux, ecart_obs: float) -> dict:
    ca, cb = composantes_pilote(xa, m), composantes_pilote(xb, m)
    out = {k: cb[k] - ca[k] for k in COMPOSANTES[:-1]}
    # Le carburant est le même pour les deux sur un même tour : il s'annule. Ce qui reste de l'écart vient du tour 1.
    out["départ et tour 1"] = ecart_obs - (cb["temps"] - ca["temps"])
    out["effet de la stratégie"] = sum(out[k] for k in STRATEGIE)
    return out


def pertes_par_arret(x: pd.DataFrame, m: ModeleNiveaux) -> list[dict]:
    """Perte de chaque arrêt : tour d'entrée et tour de sortie, moins les deux tours normaux prédits."""
    pertes = composantes_pilote(x, m)["pertes"]
    sorties = x.loc[x["sortie_stands"] & (x["tour"] >= 2), "tour"]
    return [{"pilote": x["pilote"].iloc[0], "tour_entree": int(t - 1), "perte_s": pertes.get(t - 1, np.nan) + pertes[t]}
            for t in sorties]


def decomposer(df: pd.DataFrame, total_tours: int, a: str, b: str, ecart_obs: float, carb: Carburant = Carburant(),
               seuils: Seuils = Seuils(), variante: str = "pilote", tirages: int = 2000, graine: int = 2025) -> dict:
    """Écart final de b sur a par composante ; bootstrap des relais des autres pilotes, ceux de a et b fixes."""
    if variante == "tendance":
        carb = Carburant(carb.depart_kg, 0.0)
    d = preparer_regression(df, total_tours, carb, garder_trafic=True)
    m = ajuster_niveaux(d, seuils, variante)
    xa, xb = (tours_du_pilote(df, p, total_tours, carb) for p in (a, b))
    point = difference(xa, xb, m, ecart_obs)

    rng = np.random.default_rng(graine)
    fixes = d[d["pilote"].isin([a, b])]
    groupes = [[g for _, g in gp.groupby("id_relais")] for p, gp in d.groupby("pilote") if p not in (a, b)]
    tirs, echecs = [], 0
    for _ in range(tirages):
        parts = [fixes]
        for k, g in enumerate(groupes):
            for j, i in enumerate(rng.integers(0, len(g), len(g))):
                # Un relais tiré deux fois devient deux relais distincts (sinon la variante « relais » les fusionne).
                parts.append(g[i].assign(id_relais=g[i]["id_relais"] + f"#{j}"))
        try:
            r = difference(xa, xb, ajuster_niveaux(pd.concat(parts), seuils, variante, regroupe=False), ecart_obs)
        except (np.linalg.LinAlgError, ValueError, KeyError):
            echecs += 1
            continue
        tirs.append(r)
    tirs = pd.DataFrame(tirs)
    table = pd.DataFrame({"composante": list(point), "valeur_s": list(point.values()),
                          "ic_bas": [tirs[k].quantile(0.025) for k in point],
                          "ic_haut": [tirs[k].quantile(0.975) for k in point]})
    return {"table": table, "modele": m, "tirages_valides": len(tirs), "tirages_echoues": echecs,
            "pertes_arrets": pd.DataFrame(pertes_par_arret(xa, m) + pertes_par_arret(xb, m))}
