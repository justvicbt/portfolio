"""Réglage de l'écart de cotation (spread) et de la marge de prise (edge) du bot marginal.

Le réglage se fait sur des donnes d'entraînement (graine 2), jamais sur celles du tournoi
(graine 1) : sinon on mesurerait la chance du réglage, pas la force du bot.
On garde la combinaison dont le pire résultat (borne basse de l'intervalle à 95 %) contre
tous les adversaires du zoo est le meilleur : c'est l'objectif du projet, gagner contre tous.

Usage : python3 -m figgie.tune --deals 150
"""
import argparse
import itertools
import json
from multiprocessing import Pool

from figgie.bots import ZOO, MarginalBot
from figgie.evaluate import duplicate_match, mean_ci

OPPONENTS = [name for name in ZOO if name != MarginalBot.name]


def _run(job):
    spread, edge, opponent, deals, seed = job
    bot = type("Tuned", (MarginalBot,), {"spread": spread, "edge": edge})
    return spread, edge, opponent, mean_ci(duplicate_match(bot, ZOO[opponent], deals, seed=seed))


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--deals", type=int, default=150)
    parser.add_argument("--seed", type=int, default=2)
    parser.add_argument("--spreads", type=int, nargs="+", default=[1, 2, 3, 4, 5])
    parser.add_argument("--edges", type=int, nargs="+", default=[0, 1, 2])
    parser.add_argument("--out", help="fichier JSON où écrire les résultats")
    args = parser.parse_args()

    grid = list(itertools.product(args.spreads, args.edges))
    jobs = [(sp, ed, opp, args.deals, args.seed) for sp, ed in grid for opp in OPPONENTS]
    with Pool() as pool:  # un calcul par cœur
        results = pool.map(_run, jobs)
    rows = []
    for spread, edge in grid:
        scores = {opp: ci for sp, ed, opp, ci in results if (sp, ed) == (spread, edge)}
        rows.append({"spread": spread, "edge": edge, "scores": scores,
                     "worst_low": min(lo for _, lo, _ in scores.values())})
    print("| spread | edge | " + " | ".join(OPPONENTS) + " | pire borne basse |")
    print("|---" * (len(OPPONENTS) + 3) + "|")
    for r in rows:
        cells = " | ".join(f"{r['scores'][o][0]:+.1f}" for o in OPPONENTS)
        print(f"| {r['spread']} | {r['edge']} | {cells} | {r['worst_low']:+.1f} |")
    best = max(rows, key=lambda r: r["worst_low"])
    print(f"\nRetenu : spread {best['spread']}, edge {best['edge']}")
    if args.out:
        with open(args.out, "w") as f:
            json.dump({"args": vars(args), "rows": rows, "best": best}, f, indent=2)


if __name__ == "__main__":
    main()
