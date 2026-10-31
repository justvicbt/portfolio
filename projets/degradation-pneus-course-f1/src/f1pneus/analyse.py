from dataclasses import replace

import pandas as pd

from .config import SCENARIOS_CARBURANT, Carburant, Seuils
from .decomposition import decomposer
from .donnees import preparer
from .modele import pentes_gommes, preparer_regression


def fr(x: float, nd: int = 2) -> str:
    return f"{x:.{nd}f}".replace(".", ",").replace("-", "−")


def scenarios(brut: dict, base: pd.DataFrame, total: int, seuils: Seuils, carb: Carburant,
              pilotes: tuple[str, str]) -> pd.DataFrame:
    """Pente par gomme (estimée dans les relais) sous chaque hypothèse, une à la fois, le reste à la référence."""
    ref_df = preparer(brut, base, seuils)
    lignes = []

    def ajouter(groupe, nom, df=ref_df, c=carb, s=seuils, trafic=False, exclure=None, **kw):
        d = preparer_regression(df, total, c, garder_trafic=trafic)
        if exclure:
            d = d[d["pilote"] != exclure]
        t = pentes_gommes(d, s, **kw)
        t.insert(0, "scenario", nom)
        t.insert(0, "groupe", groupe)
        lignes.append(t)

    ajouter("référence", f"Référence : {fr(carb.s_par_kg)} s/kg, air libre {fr(seuils.air_libre_s, 1)} s, "
                         f"aberrants à {fr(seuils.aberrant_s, 1)} s")
    ajouter("carburant", "Aucune correction du carburant", c=replace(carb, s_par_kg=0.0))
    for k in SCENARIOS_CARBURANT:
        if k != carb.s_par_kg:
            ajouter("carburant", f"{fr(k)} s/kg", c=replace(carb, s_par_kg=k))
    for kg in (95.0, 110.0):
        ajouter("carburant", f"{fr(kg, 0)} kg au départ", c=replace(carb, depart_kg=kg))
    ajouter("carburant", "Tendance estimée sur les données (sans hypothèse)", c=replace(carb, s_par_kg=0.0),
            tendance=True)
    ajouter("trafic", "Tours dans le trafic gardés", trafic=True)
    ajouter("trafic", "Trafic gardé, avec un indicateur", trafic=True, indicateur_trafic=True)
    for a in (1.0, 2.0, 3.0):
        s = replace(seuils, air_libre_s=a)
        ajouter("trafic", f"Air libre à {fr(a, 1)} s", df=preparer(brut, base, s), s=s)
    s = replace(seuils, source_ecart="openf1")
    ajouter("trafic", "Écart à la voiture qui précède au classement", df=preparer(brut, base, s), s=s)
    for ab, nom in ((1.5, "Aberrants à 1,5 s"), (None, "Sans filtre des aberrants")):
        s = replace(seuils, aberrant_s=ab)
        ajouter("aberrants", nom, df=preparer(brut, base, s), s=s)
    for p in pilotes:
        ajouter("pilotes", f"Sans {p}", exclure=p)
    return pd.concat(lignes, ignore_index=True)


def decompositions(df: pd.DataFrame, total: int, a: str, b: str, ecart: float, seuils: Seuils, carb: Carburant,
                   tirages: int) -> tuple[pd.DataFrame, dict]:
    tables, reference = [], None
    ks = sorted(set(SCENARIOS_CARBURANT) | {carb.s_par_kg})
    hypotheses = [("pilote", k) for k in ks] + [("relais", k) for k in ks]
    hypotheses.append(("tendance", None))
    for variante, k in hypotheses:
        c = carb if k is None else replace(carb, s_par_kg=k)
        r = decomposer(df, total, a, b, ecart, c, seuils, variante, tirages)
        t = r["table"].assign(variante=variante, carburant_s_par_kg=float("nan") if k is None else k,
                              tirages_valides=r["tirages_valides"])
        tables.append(t)
        if variante == "pilote" and k == carb.s_par_kg:
            reference = r
    return pd.concat(tables, ignore_index=True), reference
