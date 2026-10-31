import numpy as np
import pandas as pd
import pytest
from fabrique import T0, tours

from f1pneus.config import Carburant, Seuils
from f1pneus.nettoyage import (ajouter_meteo, ajouter_pneus, corriger_carburant, ecart_openf1, ecart_physique,
                               etat_piste, fenetres_neutralisation, marquer, tableau_retraits, tours_annules)


def _t(s):
    return (T0 + pd.Timedelta(seconds=s)).isoformat()


def test_chaque_filtre_retire_son_tour_et_est_compte():
    df = tours([{"tour": n} for n in range(1, 13)])
    df.loc[df["tour"] == 3, "entree_stands"] = True
    df.loc[df["tour"] == 4, "sortie_stands"] = True
    df.loc[df["tour"] == 5, "neutralisation"] = "VSC"
    df.loc[df["tour"] == 6, "neutralisation"] = "JAUNE"
    df.loc[df["tour"] == 8, "pluie"] = True
    df.loc[df["tour"] == 9, "gomme"] = "INTERMEDIATE"
    df.loc[df["tour"] == 10, "duree"] = 81.5        # 1,5 s au-dessus de ses voisins : aberrant
    df.loc[df["tour"] == 11, ["ecart_phys_debut"]] = 0.9
    out = marquer(df, annules={(1, 7)})
    attendu = {1: "tour 1", 3: "entrée aux stands", 4: "sortie des stands", 5: "neutralisation",
               6: "drapeau jaune", 7: "tour annulé", 8: "pluie", 9: "gomme pluie ou inconnue", 10: "aberrant"}
    assert dict(zip(out["tour"], out["retrait"])) == {n: attendu.get(n, "") for n in range(1, 13)}
    assert out.loc[out["tour"] == 11, "trafic"].item()           # le trafic n'est pas un retrait
    t = tableau_retraits(out).loc["AAA"]
    assert t["tours"] == 12 and t["gardé"] == 3 and t["dont trafic"] == 1 and t["air libre"] == 2
    assert all(t[m] == 1 for m in attendu.values())


def test_filtres_parametrables():
    df = tours([{"tour": n} for n in range(1, 9)])
    df.loc[df["tour"] == 4, "neutralisation"] = "JAUNE"
    df.loc[df["tour"] == 6, "duree"] = 81.2
    df.loc[df["tour"] == 7, "ecart_phys_debut"] = 1.8
    out = marquer(df, set(), Seuils(retirer_jaunes=False, aberrant_s=1.5, air_libre_s=2.0))
    assert (out["retrait"] != "").sum() == 1                       # seulement le tour 1
    assert out.loc[out["tour"] == 7, "trafic"].item()
    assert not marquer(df, set(), Seuils(aberrant_s=None))["retrait"].eq("aberrant").any()


def test_aberrants_ne_rejettent_pas_la_fin_d_un_relais_use():
    # 30 tours qui perdent 0,1 s par tour : 2,9 s d'écart entre le début et la fin, rien d'aberrant.
    df = tours([{"tour": n, "duree": 80 + 0.1 * n} for n in range(1, 31)])
    assert not marquer(df, set())["retrait"].eq("aberrant").any()


def test_fenetres_de_neutralisation_et_tour_de_relance():
    rc = [{"date": _t(100), "category": "SafetyCar", "message": "SAFETY CAR DEPLOYED"},
          {"date": _t(300), "category": "SafetyCar", "message": "SAFETY CAR IN THIS LAP"},
          {"date": _t(380), "category": "Flag", "flag": "GREEN", "scope": "Track", "message": "TRACK CLEAR"},
          {"date": _t(600), "category": "SafetyCar", "message": "VIRTUAL SAFETY CAR DEPLOYED"},
          {"date": _t(650), "category": "SafetyCar", "message": "VIRTUAL SAFETY CAR ENDING"},
          {"date": _t(900), "category": "Flag", "flag": "YELLOW", "scope": "Sector", "sector": 4,
           "message": "YELLOW IN TRACK SECTOR 4"}]
    f = fenetres_neutralisation(rc, Seuils(marge_neutralisation_s=30))
    assert list(f["type"]) == ["SC", "VSC", "JAUNE"]
    assert (f.iloc[0]["fin"] - T0).total_seconds() == 410           # + 30 s de relance
    assert (f.iloc[2]["fin"] - f.iloc[2]["debut"]).total_seconds() == 60   # jaune jamais refermé
    df = tours([{"tour": n} for n in range(1, 14)])
    etat = etat_piste(df, f)
    # Tours de 80 s : la VSC (600 à 680 s) touche les tours 8 et 9, le jaune (900 à 960 s) le seul tour 12.
    assert list(etat) == ["", "SC", "SC", "SC", "SC", "SC", "", "VSC", "VSC", "", "", "JAUNE", ""]


def test_tour_annule_par_le_temps_ou_par_l_heure_et_reintegration():
    df = tours([{"tour": n, "numero": 4, "duree": d} for n, d in ((1, 90.0), (2, 82.533), (3, 82.0), (4, 81.9))])
    rc = [{"date": _t(500), "message": "CAR 4 (NOR) TIME 1:22.533 DELETED - TRACK LIMITS AT TURN 7 LAP 3 15:42:20"},
          {"date": _t(330), "message": "CAR 4 (NOR) LAP DELETED - TRACK LIMITS AT TURN 4 LAP 4 15:40:00"}]
    assert tours_annules(rc, df) == {(4, 2), (4, 4)}  # le tour 4 est le dernier fini avant le message
    rc.append({"date": _t(600), "message": "CAR 4 (NOR) TIME 1:22.533 REINSTATED"})
    assert tours_annules(rc, df) == {(4, 4)}


def test_ecart_physique_compte_les_retardataires_et_ignore_la_voie_des_stands():
    # B passe 1,0 s derrière A, puis C (un tour de retard) passe entre les deux au tour suivant.
    t = {("A", 5): 0.0, ("B", 5): 1.0, ("A", 6): 80.0, ("C", 5): 80.6, ("B", 6): 81.2, ("D", 3): 81.0}
    df = tours([{"pilote": p, "numero": ord(p), "tour": n, "debut": T0 + pd.Timedelta(seconds=s),
                 "sortie_stands": p == "D"} for (p, n), s in t.items()])
    out = ecart_physique(df).set_index(["pilote", "tour"])
    assert out.loc[("B", 5), "ecart_phys_debut"] == pytest.approx(1.0)
    assert out.loc[("B", 5), "devant"] == "même tour"
    # D passe la ligne dans la voie des stands à 81,0 : il ne compte pas. La voiture devant B est C, en retard.
    assert out.loc[("B", 6), "ecart_phys_debut"] == pytest.approx(0.6)
    assert out.loc[("B", 6), "devant"] == "retardataire"
    assert out.loc[("B", 5), "ecart_phys_fin"] == pytest.approx(0.6)


def test_ecart_openf1_vide_pour_le_leader():
    df = tours([{"tour": 10, "numero": 4}, {"tour": 10, "numero": 81}])
    iv = [{"date": _t(720 - 2), "driver_number": 4, "interval": 0.0, "gap_to_leader": 0.0},
          {"date": _t(720 - 2), "driver_number": 81, "interval": 0.7, "gap_to_leader": 0.7}]
    out = ecart_openf1(df, iv)
    assert np.isnan(out.loc[0, "ecart_openf1_debut"])          # le leader n'est pas dans le trafic
    assert out.loc[1, "ecart_openf1_debut"] == pytest.approx(0.7)
    assert not marquer(out, set(), Seuils(source_ecart="openf1"))["trafic"].iloc[0]


def test_age_des_pneus_apres_un_arret_et_pneus_deja_utilises():
    df = tours([{"tour": n, "numero": 1} for n in range(1, 11)]).drop(columns=["relais", "gomme", "age_pneus"])
    stints = pd.DataFrame([
        {"driver_number": 1, "stint_number": 1, "compound": "MEDIUM", "lap_start": 1, "lap_end": 4,
         "tyre_age_at_start": 3},
        {"driver_number": 1, "stint_number": 2, "compound": "HARD", "lap_start": 5, "lap_end": 10,
         "tyre_age_at_start": 0}])
    out = ajouter_pneus(df, stints)
    assert list(out["age_pneus"]) == [3, 4, 5, 6, 0, 1, 2, 3, 4, 5]
    assert list(out["relais"]) == [1] * 4 + [2] * 6
    assert list(out["gomme"]) == ["MEDIUM"] * 4 + ["HARD"] * 6


def test_correction_du_carburant():
    c = Carburant(depart_kg=100, s_par_kg=0.03)
    y = corriger_carburant([80.0, 80.0, 80.0], [1, 50, 100], 100, c)
    # Masse au milieu du tour : 99,5 kg au tour 1, 50,5 au tour 50, 0,5 au dernier.
    assert y == pytest.approx([80 - 2.985, 80 - 1.515, 80 - 0.015])
    # Un temps qui baisse seulement à cause du carburant devient plat une fois corrigé.
    n = np.arange(1, 71)
    brut = 80 + 0.03 * 100 * (1 - (n - 0.5) / 70)
    assert np.ptp(corriger_carburant(brut, n, 70, c)) == pytest.approx(0, abs=1e-12)


def test_meteo_pluie_pendant_le_tour():
    df = tours([{"tour": n} for n in range(1, 4)])
    w = [{"date": _t(30), "track_temperature": 35.0, "rainfall": 0},
         {"date": _t(130), "track_temperature": 34.0, "rainfall": 1},
         {"date": _t(200), "track_temperature": 33.0, "rainfall": 0}]
    out = ajouter_meteo(df, w)
    assert list(out["pluie"]) == [False, True, False]
    assert out.loc[0, "temp_piste"] == 35.0
