"""Point d'entrée : python -m f1carte [--annee 2025] [--circuit Monza] [--pilote VER]

Télécharge le tour de qualification le plus rapide (OpenF1), aligne vitesse et positions,
calcule les indicateurs du tour et trace trois figures dans docs/.
"""
import argparse
import csv
import re
import sys
from datetime import UTC, datetime

import numpy as np

from . import openf1
from .config import RESULTS_DIR, Seuils
from .tour import aligner, indicateurs, parse_date, sections_rapides, tour_le_plus_rapide, tours_annules, zones_freinage

MARGE_S = 1.0  # demandée de chaque côté du tour, pour interpoler sans extrapoler


def fr(x: float, nd: int = 1) -> str:
    return f"{x:.{nd}f}".replace(".", ",").replace("-", "−")


def chrono(s: float) -> str:
    return f"{int(s // 60)}:{fr(s % 60, 3).zfill(6)}"


def _iso(ts: float) -> str:
    return datetime.fromtimestamp(ts, UTC).isoformat()


def _colonnes(rows: list[dict], t0: float, *champs: str) -> dict:
    rows = sorted(rows, key=lambda r: r["date"])
    out = {"t": np.array([parse_date(r["date"]) - t0 for r in rows])}
    for c in champs:
        out[c] = np.array([r[c] if r[c] is not None else np.nan for r in rows], float)
    return out


def _ecrire_csv(path, rows: list[dict]) -> None:
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)


def main() -> None:
    p = argparse.ArgumentParser(prog="python -m f1carte", description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    d = Seuils()
    p.add_argument("--annee", type=int, default=2025)
    p.add_argument("--circuit", default="Monza", help="nom court OpenF1 (circuit_short_name), ex. Suzuka, Spa-Francorchamps")
    p.add_argument("--pilote", help="code à trois lettres (ex. LEC) ; par défaut, le tour le plus rapide de la séance")
    p.add_argument("--seuil-fond", type=float, default=d.fond_pct, help="accélérateur (%%) à partir duquel on est à fond")
    p.add_argument("--seuil-rapide", type=float, default=d.rapide_ratio, help="part de la vitesse max du tour")
    p.add_argument("--duree-rapide", type=float, default=d.rapide_duree_s, help="durée minimale d'une section rapide (s)")
    p.add_argument("--freinage-baisse", type=float, default=d.freinage_baisse_kmh, help="baisse de vitesse minimale (km/h)")
    p.add_argument("--freinage-mesures", type=int, default=d.freinage_mesures, help="mesures de frein consécutives minimales")
    args = p.parse_args()
    seuils = Seuils(fond_pct=args.seuil_fond, rapide_ratio=args.seuil_rapide, rapide_duree_s=args.duree_rapide,
                    freinage_mesures=args.freinage_mesures, freinage_baisse_kmh=args.freinage_baisse)
    try:
        run(args, seuils)
    except openf1.AccesRefuse as e:
        sys.exit(f"{e}\nSi une session de F1 est en direct, relancer la commande après la fin de la session.")


def run(args, seuils: Seuils) -> None:
    from .carte import carte_vitesse, carte_zones, profil_vitesse

    sessions = openf1.get("sessions", year=args.annee, circuit_short_name=args.circuit, session_name="Qualifying")
    if not sessions:
        sys.exit(f"Aucune séance « Qualifying » trouvée pour {args.circuit} {args.annee} (nom court OpenF1 attendu).")
    sk = sessions[0]["session_key"]

    drivers = {dr["driver_number"]: dr for dr in openf1.get("drivers", session_key=sk)}
    numero = None
    if args.pilote:
        par_code = {dr["name_acronym"]: n for n, dr in drivers.items()}
        if args.pilote.upper() not in par_code:
            sys.exit(f"Pilote {args.pilote} absent de cette séance. Codes : {', '.join(sorted(par_code))}")
        numero = par_code[args.pilote.upper()]

    laps = openf1.get("laps", session_key=sk)
    annules = tours_annules(openf1.get("race_control", session_key=sk), laps)
    lap = tour_le_plus_rapide(laps, annules, numero)
    num, duree = lap["driver_number"], lap["lap_duration"]
    code = drivers.get(num, {}).get("name_acronym", str(num))
    t0 = parse_date(lap["date_start"])
    fenetre = {"session_key": sk, "driver_number": num, "date>": _iso(t0 - MARGE_S), "date<": _iso(t0 + duree + MARGE_S)}
    car = _colonnes(openf1.get("car_data", **fenetre), t0, "speed", "throttle", "brake")
    loc = _colonnes(openf1.get("location", **fenetre), t0, "x", "y")
    print(f"Tours annulés (pilote, tour) : {sorted(annules)}")
    print(f"Tour : {code}, tour {lap['lap_number']}, {chrono(duree)} | car_data {len(car['t'])} mesures, "
          f"location {len(loc['t'])} mesures")

    tour = aligner(car, loc, duree, seuils.trou_max_s)
    ind = indicateurs(tour, seuils)
    rapides = sections_rapides(tour, seuils)
    freinages = zones_freinage(tour, seuils)

    prefixe = f"{re.sub(r'[^a-z0-9]+', '-', args.circuit.lower())}_{args.annee}_{code.lower()}"
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    resume = {"circuit": args.circuit, "annee": args.annee, "pilote": code, "tour": lap["lap_number"],
              "temps_s": duree, **{k: round(v, 4) for k, v in ind.items()},
              "zones_freinage": len(freinages), "sections_rapides": len(rapides)}
    _ecrire_csv(RESULTS_DIR / f"{prefixe}_indicateurs.csv", [resume])
    d0 = tour.distance[0]
    zones = [{"type": "freinage", "numero": i, "debut_m": round(z["distance_m"] - d0),
              "fin_m": round(tour.distance[z["fin"]] - d0), "vitesse_entree_kmh": round(z["vitesse_entree"]),
              "vitesse_min_kmh": round(z["vitesse_min"]), "vitesse_max_kmh": ""}
             for i, z in enumerate(freinages, start=1)]
    zones += [{"type": "rapide", "numero": i, "debut_m": round(tour.distance[a] - d0),
               "fin_m": round(tour.distance[b] - d0), "vitesse_entree_kmh": round(tour.vitesse[a]),
               "vitesse_min_kmh": round(tour.vitesse[a:b + 1].min()), "vitesse_max_kmh": round(tour.vitesse[a:b + 1].max())}
              for i, (a, b) in enumerate(rapides, start=1)]
    if zones:
        _ecrire_csv(RESULTS_DIR / f"{prefixe}_zones.csv", zones)

    print(f"Vitesse max {fr(ind['vitesse_max_kmh'], 0)} km/h, min {fr(ind['vitesse_min_kmh'], 0)} km/h, "
          f"moyenne {fr(ind['vitesse_moyenne_kmh'])} km/h")
    print(f"À fond {fr(100 * ind['part_fond'])} % du temps, au freinage {fr(100 * ind['part_freinage'])} % ; "
          f"{len(freinages)} zones de freinage, {len(rapides)} sections rapides")
    print(f"Mesures gardées {ind['mesures']}, retirées {ind['mesures_retirees']}, {fr(ind['frequence_hz'])} Hz en moyenne, "
          f"écart max {fr(ind['ecart_max_s'], 2)} s")
    print(f"Distance intégrée {fr(ind['distance_vitesse_m'], 0)} m ; longueur du tracé x, y "
          f"{fr(ind['longueur_xy'], 0)} unités ; rapport {fr(ind['ratio_xy_sur_m'], 2)} unité par mètre")
    for i, z in enumerate(freinages, start=1):
        print(f"  freinage {i} : à {fr(z['distance_m'] - d0, 0)} m, {fr(z['vitesse_entree'], 0)} -> "
              f"{fr(z['vitesse_min'], 0)} km/h")

    nom_circuit = sessions[0].get("circuit_short_name", args.circuit)
    source = (f"Source : OpenF1, car_data (vitesse, frein) et location (x, y), {fr(ind['frequence_hz'])} mesures "
              f"par seconde en moyenne.\nPics de vitesse et débuts de freinage approximatifs.")
    sujet = f"\n{nom_circuit} {args.annee}, qualifications : {code}, tour {lap['lap_number']}, {chrono(duree)}"
    paths = [
        carte_vitesse(tour, f"Vitesse sur le tour{sujet}", source, f"{prefixe}_carte_vitesse.png"),
        carte_zones(tour, rapides, freinages, f"Sections rapides et zones de freinage{sujet}", source, seuils,
                    f"{prefixe}_carte_zones.png"),
        profil_vitesse(tour, rapides, freinages, f"Profil de vitesse le long du tour{sujet}", source, f"{prefixe}_profil_vitesse.png"),
    ]
    print("Figures :", *paths, sep="\n  ")


if __name__ == "__main__":
    main()
