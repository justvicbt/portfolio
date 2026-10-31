from dataclasses import dataclass

import numpy as np
import pandas as pd
import statsmodels.api as sm

from .config import GOMMES_SECHES, Carburant, Seuils
from .nettoyage import corriger_carburant

MIN_TOURS_DANS_RELAIS = 3  # en dessous, un relais n'apporte presque rien à une pente estimée dans le relais


def preparer_regression(df: pd.DataFrame, total_tours: int, carb: Carburant, garder_trafic: bool) -> pd.DataFrame:
    d = df[df["retrait"] == ""].copy()
    if not garder_trafic:
        d = d[~d["trafic"]]
    d["y"] = corriger_carburant(d["duree"], d["tour"], total_tours, carb)
    d["id_relais"] = d["pilote"] + "-" + d["relais"].astype(str)
    d["age_pneus"] = d["age_pneus"].astype(float)
    taille = d.groupby("id_relais")["tour"].transform("size")
    return d[taille >= MIN_TOURS_DANS_RELAIS]


def gommes_estimables(d: pd.DataFrame, seuils: Seuils) -> list[str]:
    g = d.groupby("gomme").agg(relais=("id_relais", "nunique"), pilotes=("pilote", "nunique"))
    ok = g[(g["relais"] >= seuils.min_relais_gomme) & (g["pilotes"] >= seuils.min_pilotes_gomme)].index
    return [c for c in GOMMES_SECHES if c in ok]


def _indicatrices(serie: pd.Series, prefixe: str, reference=None) -> pd.DataFrame:
    dum = pd.get_dummies(serie, prefix=prefixe, prefix_sep=":", dtype=float)
    if reference is not None:
        dum = dum.drop(columns=f"{prefixe}:{reference}")
    return dum


def _pentes(d: pd.DataFrame, gommes: list[str]) -> pd.DataFrame:
    return pd.DataFrame({f"pente:{c}": d["age_pneus"] * (d["gomme"] == c) for c in gommes}, index=d.index)


def _ols_regroupe(y, X: pd.DataFrame, groupes):
    # Erreurs regroupées par relais et loi de Student à G - 1 degrés de liberté : peu de relais par gomme.
    return sm.OLS(np.asarray(y, float), X.astype(float)).fit(
        cov_type="cluster", cov_kwds={"groups": pd.factorize(groupes)[0]}, use_t=True)


def pentes_gommes(d: pd.DataFrame, seuils: Seuils, tendance: bool = False,
                  indicateur_trafic: bool = False) -> pd.DataFrame:
    """Pente par gomme, estimée à l'intérieur des relais (un niveau propre à chaque relais).

    Avec `tendance`, le niveau est par pilote et par gomme, et un terme en numéro de tour estime ensemble
    l'allègement et l'évolution de la piste : c'est identifiable parce que l'âge repart de zéro à chaque arrêt.
    """
    gommes = gommes_estimables(d, seuils)
    d = d[d["gomme"].isin(gommes)]
    if tendance:
        X = pd.concat([_indicatrices(d["pilote"], "pilote"),
                       _indicatrices(d["gomme"], "gomme", gommes[0]),
                       _pentes(d, gommes), d[["tour"]].astype(float).rename(columns={"tour": "tendance"})], axis=1)
    else:
        X = pd.concat([_indicatrices(d["id_relais"], "relais"), _pentes(d, gommes)], axis=1)
    if indicateur_trafic:
        X["trafic"] = d["trafic"].astype(float)
    res = _ols_regroupe(d["y"], X, d["id_relais"])
    ic = res.conf_int(0.05)
    lignes = []
    for c in gommes:
        k = f"pente:{c}"
        sous = d[d["gomme"] == c]
        lignes.append({"gomme": c, "pente": res.params[k], "erreur_std": res.bse[k], "ic_bas": ic.loc[k, 0],
                       "ic_haut": ic.loc[k, 1], "tours": len(sous), "relais": sous["id_relais"].nunique(),
                       "pilotes": sous["pilote"].nunique(), "ddl": int(res.df_resid),
                       "tendance": res.params.get("tendance", np.nan),
                       "cout_trafic": res.params.get("trafic", np.nan)})
    return pd.DataFrame(lignes)


def pentes_relais(d: pd.DataFrame, seuils: Seuils) -> pd.DataFrame:
    """Pente de chaque relais seul. Erreurs de Newey-West : les tours successifs d'un relais se ressemblent."""
    lignes = []
    for (pilote, relais), g in d.groupby(["pilote", "relais"]):
        g = g.sort_values("tour")
        n = len(g)
        ligne = {"pilote": pilote, "relais": int(relais), "gomme": g["gomme"].iloc[0], "tours": n,
                 "premier_tour": int(g["tour"].min()), "dernier_tour": int(g["tour"].max()),
                 "age_min": int(g["age_pneus"].min()), "age_max": int(g["age_pneus"].max()),
                 "affichable": n >= seuils.min_tours_relais}
        if n >= MIN_TOURS_DANS_RELAIS and g["age_pneus"].nunique() > 1:
            X = sm.add_constant(g["age_pneus"].to_numpy(float))
            res = sm.OLS(g["y"].to_numpy(float), X).fit(cov_type="HAC", cov_kwds={"maxlags": 2}, use_t=True)
            ic = res.conf_int(0.05)
            ligne |= {"pente": res.params[1], "erreur_std": res.bse[1], "ic_bas": ic[1, 0], "ic_haut": ic[1, 1],
                      "constante": res.params[0]}
        lignes.append(ligne)
    return pd.DataFrame(lignes)


@dataclass
class ModeleNiveaux:
    """Temps corrigé = niveau + pente de la gomme × âge + coût du trafic.

    Variante « pilote » : niveau du pilote + niveau de la gomme (l'écart entre gommes est estimé).
    Variante « relais » : un niveau par relais ; la pente vient alors seulement de l'intérieur des relais.
    Variante « tendance » : comme « pilote », plus un terme en numéro de tour estimé sur les données, à la place
    de l'hypothèse de carburant (il mélange allègement et évolution de la piste).
    """
    variante: str
    gommes: list[str]
    noms: list[str]
    coef: np.ndarray
    resultat: object = None

    @property
    def p(self) -> dict:
        return dict(zip(self.noms, self.coef))


def matrice_niveaux(d: pd.DataFrame, gommes: list[str], variante: str) -> pd.DataFrame:
    duel = d["trafic"] & (d["devant"] != "retardataire")
    if variante in ("pilote", "tendance"):
        niveaux = [_indicatrices(d["pilote"], "pilote"), _indicatrices(d["gomme"], "gomme", gommes[0])]
        if variante == "tendance":
            niveaux.append(d[["tour"]].astype(float).rename(columns={"tour": "tendance"}))
    else:
        niveaux = [_indicatrices(d["id_relais"], "relais")]
    X = pd.concat(niveaux + [_pentes(d, gommes),
                             pd.DataFrame({"trafic_duel": duel.astype(float),
                                           "trafic_retard": (d["trafic"] & ~duel).astype(float)},
                                          index=d.index)], axis=1)
    # Une course sans retardataire (ou sans trafic) laisse une colonne vide : on la retire, son effet vaut 0.
    return X.loc[:, (X != 0).any()]


def ajuster_niveaux(d: pd.DataFrame, seuils: Seuils, variante: str = "pilote", regroupe: bool = True) -> ModeleNiveaux:
    gommes = gommes_estimables(d, seuils)
    d = d[d["gomme"].isin(gommes)]
    X = matrice_niveaux(d, gommes, variante)
    if regroupe:
        res = _ols_regroupe(d["y"], X, d["id_relais"])
        return ModeleNiveaux(variante, gommes, list(X.columns), res.params.to_numpy(), res)
    A = X.to_numpy(float)
    if np.linalg.matrix_rank(A) < A.shape[1]:
        raise np.linalg.LinAlgError("modèle non identifiable sur cet échantillon")
    coef, *_ = np.linalg.lstsq(A, d["y"].to_numpy(float), rcond=None)
    return ModeleNiveaux(variante, gommes, list(X.columns), coef)
