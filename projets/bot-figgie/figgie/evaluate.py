"""Évaluation par donnes dupliquées contre le zoo d'adversaires.

Une « donne dupliquée » : la même distribution de cartes est rejouée autant de fois
qu'il y a de sièges, et le bot testé passe par chacun. La chance de la donne s'annule :
il reste la différence de jeu.

Usage : python3 -m figgie.evaluate --candidate bayesien --deals 300
"""
import argparse
import json
import statistics

from figgie.bots import ZOO
from figgie.engine import play_round


def mean_ci(values):
    """Moyenne et intervalle de confiance à 95 % (approximation normale)."""
    if len(values) < 2:
        raise ValueError("il faut au moins 2 valeurs")
    mean = statistics.fmean(values)
    half = 1.96 * statistics.stdev(values) / len(values) ** 0.5
    return mean, mean - half, mean + half


def duplicate_match(candidate, opponent, n_deals, n_players=4, seed=0, duration=240.0, log_file=None):
    """Gain moyen du candidat sur chaque donne (moyenne sur toutes les rotations de sièges)."""
    per_deal = []
    for d in range(n_deals):
        # mêmes donnes pour tous les adversaires (comparaison plus juste), sans chevauchement entre graines voisines
        deal_seed = seed * 1_000_000 + d
        total = 0.0
        for seat in range(n_players):
            bots = [opponent] * n_players
            bots[seat] = candidate
            result = play_round(bots, seed=deal_seed, duration=duration)
            total += result.profits[seat]
            if log_file:
                log_file.write(json.dumps(result.log) + "\n")
        per_deal.append(total / n_players)
    return per_deal


def zoo_report(candidate, n_deals, n_players=4, seed=0, duration=240.0, log_file=None):
    """Pour chaque adversaire du zoo, sauf le candidat lui-même : (moyenne, borne basse, borne haute) du gain par manche."""
    return {
        name: mean_ci(duplicate_match(candidate, opp, n_deals, n_players, seed, duration, log_file))
        for name, opp in ZOO.items() if opp is not candidate
    }


GATE_REFERENCES = ("heuristique", "sniper")


def gate(report):
    """Règle d'entrée : un bot est refusé s'il ne bat pas nettement chaque référence (IC entièrement au-dessus de 0).
    Une référence absente du rapport (parce que c'est elle le candidat) est ignorée ; None s'il n'en reste aucune."""
    refs = [name for name in GATE_REFERENCES if name in report]
    if not refs:
        return None
    return all(report[name][1] > 0 for name in refs)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--candidate", default="bayesien", choices=sorted(ZOO))
    parser.add_argument("--deals", type=int, default=300)
    parser.add_argument("--players", type=int, default=4, choices=(4, 5))
    parser.add_argument("--duration", type=float, default=240.0, help="durée d'une manche en secondes")
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--logs", help="fichier JSONL où écrire le journal de chaque manche")
    parser.add_argument("--out", help="fichier JSON où écrire le rapport")
    args = parser.parse_args()
    if args.deals < 2:
        parser.error("--deals doit valoir au moins 2 (il faut 2 valeurs pour un intervalle de confiance)")

    log_file = open(args.logs, "w") if args.logs else None
    try:
        report = zoo_report(ZOO[args.candidate], args.deals, args.players, args.seed, args.duration, log_file)
    finally:
        if log_file:
            log_file.close()

    print(f"Candidat : {args.candidate} | {args.players} joueurs | {args.deals} donnes x {args.players} sièges\n")
    print("| Adversaires (x{}) | Gain moyen $/manche | IC 95 % |".format(args.players - 1))
    print("|---|---|---|")
    for name, (mean, low, high) in report.items():
        print(f"| {name} | {mean:+.2f} | [{low:+.2f} ; {high:+.2f}] |")
    worst = min(report, key=lambda k: report[k][0])
    print(f"\nPire adversaire : {worst} ({report[worst][0]:+.2f} $/manche)")
    verdict = gate(report)
    refs = [name for name in GATE_REFERENCES if name in report]
    print(f"Porte (bat {' et '.join(refs) or 'les références'}) :", "sans objet" if verdict is None else "ACCEPTÉ" if verdict else "REFUSÉ")
    if args.out:
        with open(args.out, "w") as f:
            json.dump({"args": vars(args), "report": report, "worst": worst, "gate": gate(report)}, f, indent=2)


if __name__ == "__main__":
    main()
