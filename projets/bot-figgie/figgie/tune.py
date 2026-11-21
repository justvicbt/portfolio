"""Réglage de l'écart de cotation (spread) et de la marge de prise (edge) d'un bot (le marginal par défaut).

Le réglage se fait sur des donnes d'entraînement (graine 2), jamais sur celles du tournoi
(graine 1) : sinon on mesurerait la chance du réglage, pas la force du bot.
On garde la combinaison dont le pire résultat (borne basse de l'intervalle à 95 %) contre
tous les adversaires du zoo est le meilleur : c'est l'objectif du projet, gagner contre tous.

Avec --minority (phase 4), l'objectif compte aussi chaque adversaire seul face à des copies du bot
réglé : un réglage qui se fait exploiter quand il est nombreux à la table est pénalisé.

Usage : python3 -m figgie.tune --deals 150                                   (phase 2)
        python3 -m figgie.tune --bot lecteur_ligue --players 5 --minority    (phase 4)
"""
import argparse
import itertools
import json
from multiprocessing import Pool

from figgie.bots import ZOO, ValueBot
from figgie.evaluate import CANDIDATES, duplicate_match, mean_ci, minority_report

TUNABLE = sorted(name for name, bot in CANDIDATES.items() if issubclass(bot, ValueBot))  # bots qui ont un spread


def _run(job):
    """Gain du bot réglé face à des copies d'un adversaire ; avec `alone`, gain de l'adversaire seul
    face à des copies du bot réglé (test de minorité), compté en négatif : plus il gagne, pire c'est."""
    bot_name, setting, opponent, alone, deals, players, seed = job
    spread, edge, spread_late, edge_late = setting
    bot = type("Tuned", (CANDIDATES[bot_name],), {"spread": spread, "edge": edge,
                                                  "spread_late": spread_late, "edge_late": edge_late})
    if alone:  # même définition que la règle d'entrée (evaluate.minority_report)
        mean, low, high = minority_report(bot, deals, players, seed, references=(opponent,))[opponent]
        return setting, f"{opponent} seul", (-mean, -high, -low)
    return setting, opponent, mean_ci(duplicate_match(bot, ZOO[opponent], deals, players, seed=seed))


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--deals", type=int, default=150)
    parser.add_argument("--seed", type=int, default=2)
    parser.add_argument("--bot", default="marginal", choices=TUNABLE)
    parser.add_argument("--players", type=int, default=4, choices=(4, 5))
    parser.add_argument("--minority", action="store_true", help="ajouter le test de minorité à l'objectif")
    parser.add_argument("--spreads", type=int, nargs="+", default=[1, 2, 3, 4, 5])
    parser.add_argument("--edges", type=int, nargs="+", default=[0, 1, 2])
    parser.add_argument("--spreads-late", type=int, nargs="+", default=[None],
                        help="phase 5b : spread en fin de manche (par défaut, le même qu'au début)")
    parser.add_argument("--edges-late", type=int, nargs="+", default=[None],
                        help="phase 5b : marge en fin de manche (par défaut, la même qu'au début)")
    parser.add_argument("--out", help="fichier JSON où écrire les résultats")
    args = parser.parse_args()

    grid = list(itertools.product(args.spreads, args.edges, args.spreads_late, args.edges_late))
    opponents = [name for name in ZOO if ZOO[name] is not CANDIDATES[args.bot]]
    jobs = [(args.bot, g, opp, False, args.deals, args.players, args.seed) for g in grid for opp in opponents]
    if args.minority:
        jobs += [(args.bot, g, opp, True, args.deals, args.players, args.seed) for g in grid for opp in opponents]
    with Pool() as pool:  # un calcul par cœur
        results = pool.map(_run, jobs)
    rows = []
    for g in grid:
        scores = {opp: ci for setting, opp, ci in results if setting == g}
        rows.append({"spread": g[0], "edge": g[1], "spread_late": g[2], "edge_late": g[3], "scores": scores,
                     "worst_low": min(lo for _, lo, _ in scores.values())})
    columns = list(rows[0]["scores"])
    late = lambda v: "=" if v is None else v  # « = » : même valeur qu'au début
    print("| spread | edge | spread fin | edge fin | " + " | ".join(columns) + " | pire borne basse |")
    print("|---" * (len(columns) + 5) + "|")
    for r in rows:
        cells = " | ".join(f"{r['scores'][o][0]:+.1f}" for o in columns)
        print(f"| {r['spread']} | {r['edge']} | {late(r['spread_late'])} | {late(r['edge_late'])} | {cells} "
              f"| {r['worst_low']:+.1f} |")
    best = max(rows, key=lambda r: r["worst_low"])
    print(f"\nRetenu : spread {best['spread']}, edge {best['edge']}, en fin de manche spread "
          f"{late(best['spread_late'])}, edge {late(best['edge_late'])}")
    if args.out:
        with open(args.out, "w") as f:
            json.dump({"args": vars(args), "rows": rows, "best": best}, f, indent=2)


if __name__ == "__main__":
    main()
