"""Le lecteur apprend-il au fil d'une partie ? Comparaison avec et sans mémoire, manche par manche.

Les deux versions jouent les mêmes parties (donnes dupliquées) à la même table mixte. La seule
différence : la version sans mémoire oublie, à chaque manche, ce qu'elle a appris des adversaires.
Si la mémoire sert, l'écart doit grandir au fil des manches.

Usage : python3 -m figgie.memoire --deals 200 --rounds 10
"""
import argparse
import json
from multiprocessing import Pool

from figgie.bots import ReaderBot
from figgie.engine import play_match
from figgie.evaluate import CANDIDATES, mean_ci

TABLE = ("aleatoire", "heuristique", "marginal")


class ForgetfulReader(ReaderBot):
    """Le lecteur, sans mémoire : chaque manche, il repart avec une confiance égale en chacun."""
    name = "lecteur_sans_memoire"

    def end_round(self, reveal):
        pass


def _deal(job):
    """Pour une donne : gain de chaque version à chaque manche (moyenne sur les rotations) et poids finaux."""
    d, rounds, seed, table = job
    opponents = [CANDIDATES[name] for name in table]
    n = len(opponents) + 1
    out = {}
    for bot in (ReaderBot, ForgetfulReader):
        per_round = [0.0] * rounds
        weights = {}
        for seat in range(n):
            bots = opponents[:seat] + [bot] + opponents[seat:]
            match = play_match(bots, seed=seed * 1_000_000 + d, rounds=rounds)
            for r, log in enumerate(match.logs):
                per_round[r] += log["profits"][seat] / n
            if bot is ReaderBot:  # confiance finale accordée à chaque style d'adversaire
                trust = match.memories[seat]["opponents"]
                for p, opp in enumerate(bots):
                    if p != seat:  # weight() vaut 1 pour un adversaire resté muet : il compte aussi
                        weights[opp.name] = weights.get(opp.name, 0.0) + trust.weight(p) / n / table.count(opp.name)
        out[bot.name] = (per_round, weights)
    return out


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--deals", type=int, default=200)
    parser.add_argument("--rounds", type=int, default=10)
    parser.add_argument("--seed", type=int, default=1)
    parser.add_argument("--table", default=",".join(TABLE), help="adversaires, séparés par des virgules")
    parser.add_argument("--out", help="fichier JSON où écrire les résultats")
    args = parser.parse_args()
    table = tuple(args.table.split(","))

    with Pool() as pool:
        deals = pool.map(_deal, [(d, args.rounds, args.seed, table) for d in range(args.deals)])

    print(f"Table : lecteur + {', '.join(table)} | {args.deals} parties de {args.rounds} manches, donnes dupliquées\n")
    print("| Manche | avec mémoire | sans mémoire | écart (IC 95 %) |")
    print("|---|---|---|---|")
    rows = []
    for r in range(args.rounds):
        with_mem = [d[ReaderBot.name][0][r] for d in deals]
        without = [d[ForgetfulReader.name][0][r] for d in deals]
        diff = mean_ci([a - b for a, b in zip(with_mem, without)])
        rows.append({"round": r + 1, "with": mean_ci(with_mem), "without": mean_ci(without), "diff": diff})
        print(f"| {r + 1} | {rows[-1]['with'][0]:+.2f} | {rows[-1]['without'][0]:+.2f} | "
              f"{diff[0]:+.2f} [{diff[1]:+.2f} ; {diff[2]:+.2f}] |")
    # Écart global une fois la mémoire utilisable (à partir de la manche 2), moyenné par partie.
    pooled = mean_ci([sum(d[ReaderBot.name][0][r] - d[ForgetfulReader.name][0][r] for r in range(1, args.rounds))
                      / (args.rounds - 1) for d in deals])
    print(f"\nÉcart moyen des manches 2 à {args.rounds} : {pooled[0]:+.2f} $/manche [{pooled[1]:+.2f} ; {pooled[2]:+.2f}]")
    weights = {name: sum(d[ReaderBot.name][1].get(name, 0) for d in deals) / len(deals) for name in set(table)}
    print("\nConfiance moyenne en fin de partie : " + ", ".join(f"{k} {v:.2f}" for k, v in sorted(weights.items())))
    if args.out:
        with open(args.out, "w") as f:
            json.dump({"args": vars(args), "rows": rows, "pooled": pooled, "weights": weights}, f, indent=2)


if __name__ == "__main__":
    main()
