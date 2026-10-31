import numpy as np
import pandas as pd
import pytest
from fabrique import course_simulee

from f1pneus.config import Carburant, Seuils
from f1pneus.decomposition import COMPOSANTES, decomposer
from f1pneus.modele import pentes_gommes, pentes_relais, preparer_regression
from f1pneus.nettoyage import marquer

TOTAL = 60


def _prep(df):
    return marquer(df, set(), Seuils())


@pytest.mark.parametrize("graine", [1, 2, 3])
def test_la_pente_connue_est_retrouvee_malgre_bruit_carburant_et_trafic(graine):
    df, vrai = course_simulee(graine)
    d = preparer_regression(_prep(df), TOTAL, Carburant(), garder_trafic=False)
    t = pentes_gommes(d, Seuils()).set_index("gomme")
    for g, pente in vrai["pentes"].items():
        assert t.loc[g, "ic_bas"] <= pente <= t.loc[g, "ic_haut"]
        assert t.loc[g, "pente"] == pytest.approx(pente, abs=0.012)


def test_sans_les_corrections_l_estimation_est_biaisee():
    df, vrai = course_simulee(1)
    m = _prep(df)
    # Trafic gardé : les tours lents de début de relais écrasent la pente (de 0,011 et 0,014 s/tour avec cette graine).
    avec_trafic = pentes_gommes(preparer_regression(m, TOTAL, Carburant(), True), Seuils()).set_index("gomme")
    # Pas de correction : l'allègement (0,03 × 100 / 60 = 0,05 s/tour) masque la dégradation.
    sans_carb = pentes_gommes(preparer_regression(m, TOTAL, Carburant(s_par_kg=0), False), Seuils()).set_index("gomme")
    for g, pente in vrai["pentes"].items():
        assert avec_trafic.loc[g, "pente"] < pente - 0.008
        assert sans_carb.loc[g, "pente"] == pytest.approx(pente - 0.05, abs=0.012)
    # Un indicateur de trafic dans le modèle répare le premier biais et retrouve le coût du trafic.
    ind = pentes_gommes(preparer_regression(m, TOTAL, Carburant(), True), Seuils(),
                        indicateur_trafic=True).set_index("gomme")
    for g, pente in vrai["pentes"].items():
        assert ind.loc[g, "pente"] == pytest.approx(pente, abs=0.012)
    assert ind["cout_trafic"].iloc[0] == pytest.approx(0.8, abs=0.1)


def test_la_tendance_estimee_retrouve_la_pente_sans_hypothese_de_carburant():
    df, vrai = course_simulee(4)
    d = preparer_regression(_prep(df), TOTAL, Carburant(s_par_kg=0), False)
    t = pentes_gommes(d, Seuils(), tendance=True).set_index("gomme")
    for g, pente in vrai["pentes"].items():
        assert t.loc[g, "pente"] == pytest.approx(pente, abs=0.015)
    # L'allègement apparaît comme une tendance de −0,05 s par tour.
    assert t["tendance"].iloc[0] == pytest.approx(-0.05, abs=0.01)


def test_une_gomme_trop_peu_utilisee_n_a_pas_de_pente_commune():
    df, _ = course_simulee(5)
    d = preparer_regression(_prep(df), TOTAL, Carburant(), False)
    d = d[(d["gomme"] != "HARD") | d["pilote"].isin(["P00", "P02"])]   # 2 relais en dur seulement
    assert list(pentes_gommes(d, Seuils())["gomme"]) == ["MEDIUM"]


def test_pente_d_un_relais_et_seuil_d_affichage():
    df, vrai = course_simulee(6, bruit=0.05, p_trafic=0)
    d = preparer_regression(_prep(df), TOTAL, Carburant(), False)
    r = pentes_relais(d, Seuils(min_tours_relais=8))
    longs = r[r["tours"] >= 8]
    assert longs["affichable"].all() and not r[r["tours"] < 8]["affichable"].any()
    for row in longs.itertuples():
        assert row.pente == pytest.approx(vrai["pentes"][row.gomme], abs=0.02)


def test_la_decomposition_retombe_sur_l_ecart_et_retrouve_arrets_et_usure():
    df, vrai = course_simulee(7, bruit=0.15)
    m = _prep(df)
    a, b = "P00", "P01"                       # 1 arrêt contre 2 arrêts
    x = df.pivot(index="tour", columns="pilote", values="duree")
    ecart = x[b].sum() - x[a].sum()
    r = decomposer(m, TOTAL, a, b, ecart, tirages=50)
    t = r["table"].set_index("composante")["valeur_s"]
    assert sum(t[k] for k in COMPOSANTES) == pytest.approx(ecart, abs=1e-9)
    assert t["arrêts"] == pytest.approx(vrai["perte_arret"], abs=1.5)    # un arrêt de plus
    # Usure vraie : somme des (pente × âge) de b moins celle de a, du tour 2 à la fin.
    s = df[df["tour"] >= 2].assign(u=lambda d: d["gomme"].map(vrai["pentes"]) * d["age_pneus"].astype(float))
    u = s.groupby("pilote")["u"].sum()
    assert t["usure des pneus"] == pytest.approx(u[b] - u[a], abs=2.0)
    ic = r["table"].set_index("composante").loc["usure des pneus"]
    assert ic["ic_bas"] <= t["usure des pneus"] <= ic["ic_haut"]
    assert r["tirages_valides"] == 50


def test_la_decomposition_refuse_un_pilote_qui_n_a_pas_fini():
    df, _ = course_simulee(8)
    df = df[~((df["pilote"] == "P01") & (df["tour"] > 50))]
    with pytest.raises(ValueError):
        decomposer(_prep(df), TOTAL, "P00", "P01", 1.0, tirages=5)
