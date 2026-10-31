"""Point d'entrée : python -m f1pneus [--annee 2025] [--circuit Hungaroring] [--pilotes NOR PIA]

Télécharge une course (OpenF1), nettoie les tours, estime la dégradation des pneus sous plusieurs hypothèses
et décompose l'écart final entre deux pilotes. Figures dans docs/, tableaux dans docs/results/.
"""
import argparse
import re
import sys
from pathlib import Path

from . import openf1
from .analyse import decompositions, fr, scenarios
from .config import DOCS_DIR, Carburant, Seuils
from .decomposition import ecart_final
from .donnees import nombre_de_tours, preparer, telecharger, tours_de_base
from .modele import pentes_gommes, pentes_relais, preparer_regression
from .nettoyage import corriger_carburant, tableau_retraits


def main() -> None:
    p = argparse.ArgumentParser(prog="python -m f1pneus", description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    s, c = Seuils(), Carburant()
    p.add_argument("--annee", type=int, default=2025)
    p.add_argument("--circuit", default="Hungaroring", help="nom court OpenF1 (circuit_short_name)")
    p.add_argument("--pilotes", nargs=2, default=["NOR", "PIA"], metavar=("A", "B"),
                   help="les deux pilotes comparés ; l'écart est celui de B sur A")
    p.add_argument("--carburant-s-kg", type=float, default=c.s_par_kg, help="temps perdu par kg de carburant (s)")
    p.add_argument("--carburant-depart", type=float, default=c.depart_kg, help="carburant au départ (kg)")
    p.add_argument("--air-libre", type=float, default=s.air_libre_s, help="écart sur la ligne sous lequel un tour "
                   "compte comme dans le trafic (s)")
    p.add_argument("--ecart", choices=["physique", "openf1"], default=s.source_ecart,
                   help="voiture devant sur la piste, ou voiture qui précède au classement")
    p.add_argument("--aberrant", type=float, default=s.aberrant_s,
                   help="écart à la médiane glissante du relais (s) ; 0 pour ne pas filtrer")
    p.add_argument("--garder-jaunes", action="store_true", help="garder les tours sous drapeau jaune")
    p.add_argument("--garder-annules", action="store_true", help="garder les tours annulés (limites de piste)")
    p.add_argument("--min-tours-relais", type=int, default=s.min_tours_relais)
    p.add_argument("--tirages", type=int, default=2000, help="tirages du bootstrap")
    p.add_argument("--sortie", type=Path, default=DOCS_DIR, help="dossier des figures (résultats dans results/)")
    args = p.parse_args()
    seuils = Seuils(air_libre_s=args.air_libre, source_ecart=args.ecart,
                    aberrant_s=args.aberrant if args.aberrant > 0 else None,
                    retirer_jaunes=not args.garder_jaunes, retirer_annules=not args.garder_annules,
                    min_tours_relais=args.min_tours_relais)
    carb = Carburant(depart_kg=args.carburant_depart, s_par_kg=args.carburant_s_kg)
    try:
        run(args, seuils, carb)
    except openf1.AccesRefuse as e:
        sys.exit(f"{e}\nSi une session de F1 est en direct, relancer la commande après la fin de la session.")
    except ValueError as e:
        sys.exit(str(e))


def run(args, seuils: Seuils, carb: Carburant) -> None:
    from . import figures

    brut = telecharger(args.annee, args.circuit)
    total = nombre_de_tours(brut)
    base = tours_de_base(brut)
    df = preparer(brut, base, seuils)
    a, b = (x.upper() for x in args.pilotes)
    for x in (a, b):
        if x not in set(df["pilote"]):
            sys.exit(f"Pilote {x} absent de cette course. Codes : {', '.join(sorted(set(df['pilote'])))}")
    df["y"] = corriger_carburant(df["duree"], df["tour"], total, carb)

    prefixe = f"{re.sub(r'[^a-z0-9]+', '-', args.circuit.lower())}_{args.annee}"
    res_dir = args.sortie / "results"
    res_dir.mkdir(parents=True, exist_ok=True)

    retraits = tableau_retraits(df)
    retraits.to_csv(res_dir / f"{prefixe}_retraits.csv")
    print(f"{args.circuit} {args.annee} : {total} tours, {len(df)} tours chronométrés")
    print(f"Température de piste : de {fr(df['temp_piste'].min(), 1)} à {fr(df['temp_piste'].max(), 1)} °C ; "
          f"tours sous la pluie : {int(df['pluie'].sum())} ; neutralisés : {int((df['neutralisation'] != '').sum())}")
    print("Tours retirés par motif :")
    print(retraits.to_string())

    d = preparer_regression(df, total, carb, garder_trafic=False)
    gommes = pentes_gommes(d, seuils)
    relais = pentes_relais(d, seuils)
    gommes.to_csv(res_dir / f"{prefixe}_pentes_gommes.csv", index=False)
    relais.to_csv(res_dir / f"{prefixe}_pentes_relais.csv", index=False)
    print("\nPente par gomme (dans les relais, air libre) :")
    for r in gommes.itertuples():
        print(f"  {r.gomme:6s} {fr(r.pente, 3)} s/tour [{fr(r.ic_bas, 3)} ; {fr(r.ic_haut, 3)}], "
              f"{r.tours} tours, {r.relais} relais, {r.pilotes} pilotes")

    scen = scenarios(brut, base, total, seuils, carb, (a, b))
    scen.to_csv(res_dir / f"{prefixe}_scenarios_pentes.csv", index=False)
    print("\nSensibilité des pentes :")
    print(scen.pivot_table(index="scenario", columns="gomme", values="pente", sort=False).round(4).to_string())

    ecart = ecart_final(brut["session_result"], df, a, b)
    toutes, ref = decompositions(df, total, a, b, ecart, seuils, carb, args.tirages)
    toutes.to_csv(res_dir / f"{prefixe}_{a.lower()}_{b.lower()}_decomposition.csv", index=False)
    ref["pertes_arrets"].to_csv(res_dir / f"{prefixe}_{a.lower()}_{b.lower()}_arrets.csv", index=False)
    print(f"\nÉcart final de {b} sur {a} : {fr(ecart, 3)} s")
    print(f"Décomposition (niveaux par pilote et gomme, {fr(carb.s_par_kg)} s/kg, "
          f"{ref['tirages_valides']} tirages valides sur {args.tirages}) :")
    for r in ref["table"].itertuples():
        print(f"  {r.composante:26s} {fr(r.valeur_s, 2):>7s} s [{fr(r.ic_bas, 2)} ; {fr(r.ic_haut, 2)}]")
    print("Effet de la stratégie selon l'hypothèse :")
    for r in toutes[toutes["composante"] == "effet de la stratégie"].itertuples():
        k = "sans hypothèse" if r.carburant_s_par_kg != r.carburant_s_par_kg else f"{fr(r.carburant_s_par_kg)} s/kg"
        print(f"  {r.variante:8s} {k:15s} {fr(r.valeur_s, 2):>7s} s [{fr(r.ic_bas, 2)} ; {fr(r.ic_haut, 2)}]")
    print("Pertes aux arrêts :")
    for r in ref["pertes_arrets"].itertuples():
        print(f"  {r.pilote} tour {r.tour_entree} : {fr(r.perte_s, 2)} s")

    nom_course = f"{brut['session']['circuit_short_name']} {args.annee}"
    sujet = (f"{nom_course}, {a} contre {b} | carburant {fr(carb.s_par_kg)} s/kg, {fr(carb.depart_kg, 0)} kg au "
             f"départ ; trafic : écart {'sur la ligne' if seuils.source_ecart == 'physique' else 'OpenF1'} "
             f"< {fr(seuils.air_libre_s, 1)} s")
    source = "Source : OpenF1 (laps, stints, pit, intervals, race_control, weather)."
    dossier = args.sortie
    paths = [
        figures.nuage_age(df, pentes_relais(preparer_regression(df, total, carb, False), seuils), (a, b), sujet,
                          f"Droites ajustées sur les tours en air libre seulement. Intervalles de Newey-West à 95 %. "
                          f"{source}", dossier, f"{prefixe}_nuage_age_pneus.png"),
        figures.forest_relais(relais, gommes, (a, b), f"{nom_course}, tous les pilotes, tours en air libre",
                              f"Relais d'au moins {seuils.min_tours_relais} tours propres ; {a} et {b} en gras et "
                              f"marqueurs pleins. Pente commune : un niveau par relais, erreurs regroupées par relais.\n"
                              f"{source}", dossier, f"{prefixe}_pentes_relais.png"),
        figures.rythme_course(df, (a, b), f"{nom_course}, {a} contre {b}",
                              f"Trafic : écart de moins de {fr(seuils.air_libre_s, 1)} s avec la voiture devant sur la "
                              f"ligne, au début ou à la fin du tour. Tours d'arrêt coupés en haut de l'échelle.\n{source}",
                              dossier, f"{prefixe}_rythme_course.png"),
        figures.effet_corrections(scen, f"{nom_course}, tous les pilotes : une hypothèse change à la fois",
                                  "Bande et trait pointillé : estimation de référence. Pente estimée dans les relais, "
                                  f"erreurs regroupées par relais.\n{source}", dossier,
                                  f"{prefixe}_effet_corrections.png"),
        figures.decomposition(ref["table"], toutes, (a, b), ecart, sujet,
                              "Intervalles à 95 % par bootstrap des relais des autres pilotes : ils ne couvrent que "
                              "l'incertitude statistique des paramètres,\npas le choix des hypothèses ni du modèle. "
                              f"Effet de la stratégie = arrêts + niveau de la gomme + usure. {source}", dossier,
                              f"{prefixe}_{a.lower()}_{b.lower()}_decomposition.png"),
    ]
    print("\nFigures :", *paths, sep="\n  ")


if __name__ == "__main__":
    main()
