import numpy as np
import pytest

from f1carte.config import Seuils
from f1carte.tour import (Tour, aligner, indicateurs, sections_rapides, tour_le_plus_rapide, tours_annules,
                          zones_freinage)


def flux(duree=10.0, hz_car=4.0, hz_loc=3.7, decalage=0.13, vitesse=180.0):
    """Voiture en ligne droite à vitesse constante ; x = 50 m/s × t, flux décalés et de fréquences différentes."""
    tc = np.arange(-1.0, duree + 1.0, 1 / hz_car)
    tl = np.arange(-1.0 + decalage, duree + 1.0, 1 / hz_loc)
    car = {"t": tc, "speed": np.full(len(tc), vitesse), "throttle": np.full(len(tc), 100.0),
           "brake": np.zeros(len(tc))}
    loc = {"t": tl, "x": vitesse / 3.6 * tl, "y": np.zeros(len(tl))}
    return car, loc


def tour_de(vitesse, frein=None, dt=0.25):
    v = np.asarray(vitesse, float)
    t = np.arange(len(v)) * dt
    f = np.zeros(len(v), bool) if frein is None else np.asarray(frein, bool)
    dist = np.concatenate([[0.0], np.cumsum((v[1:] + v[:-1]) / 2 / 3.6 * dt)])
    return Tour(t, v, np.full(len(v), 100.0), f, np.zeros(len(v)), np.zeros(len(v)), dist, 0)


def test_alignement_interpole_les_positions_sur_les_instants_de_car_data():
    car, loc = flux()
    tour = aligner(car, loc, 10.0)
    assert tour.t[0] == 0.0 and tour.t[-1] == 10.0           # bornes exactes du tour ajoutées
    assert np.all((tour.t >= 0) & (tour.t <= 10.0))           # marge hors tour retirée
    assert tour.x == pytest.approx(50.0 * tour.t)             # position juste malgré le décalage des flux
    assert tour.retirees == 0


def test_alignement_retire_les_mesures_dans_un_trou_de_positions():
    car, loc = flux()
    trou = (loc["t"] > 4.0) & (loc["t"] < 6.5)
    loc = {k: v[~trou] for k, v in loc.items()}
    tour = aligner(car, loc, 10.0)
    avant, apres = loc["t"][loc["t"] <= 4.0].max(), loc["t"][loc["t"] >= 6.5].min()
    dans_le_trou = (car["t"] > avant) & (car["t"] < apres)
    assert not np.any((tour.t > avant) & (tour.t < apres))
    assert tour.retirees == dans_le_trou.sum() > 0
    # La distance continue de s'intégrer dans le trou : elle vaut toujours 50 m/s × t.
    assert tour.distance == pytest.approx(50.0 * tour.t)


def test_indicateurs_tour_a_vitesse_constante():
    car, loc = flux()
    ind = indicateurs(aligner(car, loc, 10.0))
    assert ind["distance_vitesse_m"] == pytest.approx(500.0)
    assert ind["vitesse_moyenne_kmh"] == pytest.approx(180.0)
    assert ind["vitesse_max_kmh"] == ind["vitesse_min_kmh"] == 180.0
    assert ind["part_fond"] == pytest.approx(1.0)
    assert ind["part_freinage"] == 0.0
    assert ind["ratio_xy_sur_m"] == pytest.approx(1.0)


def test_part_au_freinage_ponderee_par_le_temps():
    tour = tour_de([300] * 8, frein=[0, 0, 1, 1, 0, 0, 0, 0])
    # 2 intervalles de 0,25 s sur un tour de 1,75 s
    assert indicateurs(tour)["part_freinage"] == pytest.approx(0.5 / 1.75)


def test_zones_de_freinage():
    v = ([320] * 4 + [300, 250, 190, 140, 100, 90] + [150] * 4    # gros freinage : gardé
         + [200, 200, 195] + [220] * 4                              # une seule mesure : écartée
         + [230, 225, 222, 220] + [240] * 4                          # baisse de 10 km/h : écartée
         + [280, 240, 200, 200, 170, 130] + [180] * 3)               # trou d'une mesure : fusionné
    f = ([0] * 4 + [1] * 6 + [0] * 4
         + [0, 1, 0] + [0] * 4
         + [1] * 4 + [0] * 4
         + [1, 1, 1, 0, 1, 1] + [0] * 3)
    zones = zones_freinage(tour_de(v, f))
    assert len(zones) == 2
    assert zones[0]["debut"] == 4 and zones[0]["vitesse_entree"] == 320 and zones[0]["vitesse_min"] == 90
    assert zones[1]["fin"] - zones[1]["debut"] == 5
    assert zones[1]["vitesse_min"] == 130


def test_seuils_de_freinage_parametrables():
    v = [230, 225, 222, 220] + [240] * 4
    f = [1] * 4 + [0] * 4
    assert zones_freinage(tour_de(v, f)) == []
    assert len(zones_freinage(tour_de(v, f), Seuils(freinage_baisse_kmh=5))) == 1


def test_sections_rapides_seuil_relatif_et_duree_minimale():
    v = [200] * 4 + [300] * 12 + [200] * 4 + [280] * 4 + [200] * 4
    rapides = sections_rapides(tour_de(v))          # seuil 270 km/h, 2 s
    assert rapides == [(4, 15)]                     # 3 s gardées ; 1 s à 280 km/h écartée
    assert len(sections_rapides(tour_de(v), Seuils(rapide_duree_s=0.5))) == 2
    # Même profil deux fois plus lent : le seuil relatif trouve la même section.
    assert sections_rapides(tour_de(np.array(v) / 2)) == [(4, 15)]


LAPS = [
    {"driver_number": 1, "lap_number": 1, "lap_duration": None, "date_start": "2025-09-06T14:00:00+00:00"},
    {"driver_number": 1, "lap_number": 2, "lap_duration": 78.9, "date_start": "2025-09-06T14:01:30+00:00",
     "is_pit_out_lap": True},
    {"driver_number": 1, "lap_number": 3, "lap_duration": 79.4, "date_start": "2025-09-06T14:03:00+00:00"},
    {"driver_number": 16, "lap_number": 7, "lap_duration": 79.1, "date_start": "2025-09-06T14:05:00+00:00"},
    {"driver_number": 16, "lap_number": 8, "lap_duration": 95.0, "date_start": "2025-09-06T14:06:19.100+00:00"},
    {"driver_number": 16, "lap_number": 9, "lap_duration": 79.3, "date_start": "2025-09-06T14:09:00+00:00"},
    {"driver_number": 44, "lap_number": 4, "lap_duration": 79.0, "date_start": None},
]


def test_choix_du_tour_le_plus_rapide():
    lap = tour_le_plus_rapide(LAPS)
    assert (lap["driver_number"], lap["lap_number"]) == (16, 7)   # sans durée, tour de sortie, sans heure : écartés
    lap = tour_le_plus_rapide(LAPS, pilote=1)
    assert lap["lap_number"] == 3
    with pytest.raises(ValueError):
        tour_le_plus_rapide(LAPS, pilote=99)


# Comme à Monza 2025 : le "LAP n" des messages vaut le numéro OpenF1 + 1, le message suit la fin du tour.
RC = [
    {"date": "2025-09-06T14:06:30+00:00",
     "message": "CAR 16 (LEC) LAP DELETED - TRACK LIMITS AT TURN 4 LAP 8 16:06:01 (PIT)"},
    {"date": "2025-09-06T14:10:30+00:00",
     "message": "CAR 16 (LEC) TIME 1:19.300 DELETED - TRACK LIMITS AT TURN 11 LAP 10 16:10:01"},
    {"date": "2025-09-06T14:12:00+00:00", "message": "CAR 16 (LEC) TIME 1:19.300 REINSTATED"},
    {"date": "2025-09-06T14:12:30+00:00", "message": "GREEN LIGHT - PIT EXIT OPEN"},
]


def test_tour_annule_retrouve_par_l_heure_ou_par_le_temps():
    # Sans temps : dernier tour terminé avant le message (le tour 8, commencé, n'est pas fini).
    assert tours_annules(RC[:1], LAPS) == {(16, 7)}
    # Avec temps : le tour de ce temps, pas le numéro du message.
    assert tours_annules(RC[1:2], LAPS) == {(16, 9)}
    # Réintégration du temps 1:19.300.
    assert tours_annules(RC, LAPS) == {(16, 7)}


def test_tours_annules_exclus_du_choix():
    lap = tour_le_plus_rapide(LAPS, tours_annules(RC, LAPS))
    assert (lap["driver_number"], lap["lap_number"]) == (16, 9)
    lap = tour_le_plus_rapide(LAPS, tours_annules(RC[:2], LAPS))
    assert (lap["driver_number"], lap["lap_number"]) == (1, 3)
