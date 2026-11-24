"""Évaluation par donnes dupliquées contre le zoo d'adversaires.

Une « donne dupliquée » : la même distribution de cartes est rejouée autant de fois
qu'il y a de sièges, et le bot testé passe par chacun. La chance de la donne s'annule :
il reste la différence de jeu.

Usage : python3 -m figgie.evaluate --candidate bayesien --deals 300
"""
import argparse
import json
import statistics

from figgie.adapt import AdaptiveBot, AdaptiveV2Bot, AdaptiveV3Bot, AdaptiveV4Bot, AdaptiveV4bBot, AdaptiveV4cBot, \
    AdaptiveV4dBot, QuietV4cBot, QuietV4cBot30, SellOnlyV4cBot
from figgie.bots import ABNORMAL, ZOO, CorrectedMarginalBot, CountingBot, HardBot, HardBotV2, LeagueReaderBot, SiteReaderBot, ImitatorBot, \
    FundamentalistBot, FundamentalistBot35, MantisBot, SellerBot, TiltBot

# Le zoo, plus les variantes de mesure, les comportements anormaux, le candidat de la ligue (phase 4)
# et le bot adaptatif (phase 5).
CANDIDATES = {**ZOO, CorrectedMarginalBot.name: CorrectedMarginalBot, CountingBot.name: CountingBot, **ABNORMAL,
              LeagueReaderBot.name: LeagueReaderBot, SiteReaderBot.name: SiteReaderBot, AdaptiveBot.name: AdaptiveBot, AdaptiveV2Bot.name: AdaptiveV2Bot, AdaptiveV3Bot.name: AdaptiveV3Bot,
              AdaptiveV4Bot.name: AdaptiveV4Bot, AdaptiveV4bBot.name: AdaptiveV4bBot, AdaptiveV4cBot.name: AdaptiveV4cBot,
              HardBot.name: HardBot, HardBotV2.name: HardBotV2, ImitatorBot.name: ImitatorBot,
              FundamentalistBot.name: FundamentalistBot, FundamentalistBot35.name: FundamentalistBot35,
              SellerBot.name: SellerBot, MantisBot.name: MantisBot, TiltBot.name: TiltBot,
              QuietV4cBot.name: QuietV4cBot, QuietV4cBot30.name: QuietV4cBot30, SellOnlyV4cBot.name: SellOnlyV4cBot,
              AdaptiveV4dBot.name: AdaptiveV4dBot}
from figgie.engine import play_match, play_round


def mean_ci(values):
    """Moyenne et intervalle de confiance à 95 % (approximation normale)."""
    if len(values) < 2:
        raise ValueError("il faut au moins 2 valeurs")
    mean = statistics.fmean(values)
    half = 1.96 * statistics.stdev(values) / len(values) ** 0.5
    return mean, mean - half, mean + half


def duplicate_match(candidate, opponent, n_deals, n_players=None, seed=0, duration=240.0, log_file=None, rounds=1,
                    first_deal=0, single_quote=False):
    """Gain moyen du candidat par manche, pour chaque donne (moyenne sur toutes les rotations de sièges).

    `opponent` : une classe (table de `n_players` copies, 4 par défaut) ou une liste de classes (table mixte).
    `rounds` : nombre de manches par partie ; avec plus d'une manche, chaque donne est une partie
    entière, rejouée à chaque rotation, et les bots gardent leur mémoire d'une manche à l'autre.
    `first_deal` : numéro de la première donne, pour couper un long calcul en morceaux parallèles.
    `single_quote` : règle du site (phase 5c), une nouvelle offre doit battre celle qui est affichée.
    """
    if isinstance(opponent, (list, tuple)):
        opponents = list(opponent)
        if n_players not in (None, len(opponents) + 1):
            raise ValueError(f"{len(opponents)} adversaires : la table a {len(opponents) + 1} joueurs, pas {n_players}")
    else:
        opponents = [opponent] * ((n_players or 4) - 1)
    n_players = len(opponents) + 1
    per_deal = []
    for d in range(first_deal, first_deal + n_deals):
        # mêmes donnes pour tous les adversaires (comparaison plus juste), sans chevauchement entre graines voisines
        deal_seed = seed * 1_000_000 + d
        total = 0.0
        for seat in range(n_players):
            bots = opponents[:seat] + [candidate] + opponents[seat:]
            if rounds == 1:
                result = play_round(bots, seed=deal_seed, duration=duration, single_quote=single_quote)
                profit, logs = result.profits[seat], [result.log]
            else:
                match = play_match(bots, seed=deal_seed, rounds=rounds, duration=duration, single_quote=single_quote)
                profit, logs = match.profits[seat] / rounds, match.logs
            total += profit
            if log_file:
                for log in logs:
                    log_file.write(json.dumps(log) + "\n")
        per_deal.append(total / n_players)
    return per_deal


def mixed_gap(reference, candidate, filler, n_deals, n_players=4, seed=0, duration=240.0, rounds=1, first_deal=0,
              single_quote=False):
    """Phase 5i, table mixte : la référence, le candidat et des copies de `filler` à la même table. Pour chaque donne,
    gain de la référence moins gain du candidat, lus dans la même partie, en moyenne sur les rotations de
    [référence, candidat, remplissants...] puis de [candidat, référence, remplissants...] : chacun passe par chaque
    siège, devant et derrière l'autre."""
    per_deal = []
    for d in range(first_deal, first_deal + n_deals):
        deal_seed = seed * 1_000_000 + d  # mêmes donnes que duplicate_match
        gaps = []
        for swapped in (False, True):
            base = [candidate, reference] if swapped else [reference, candidate]
            base += [filler] * (n_players - 2)
            for shift in range(n_players):
                bots = base[shift:] + base[:shift]
                first, second = (-shift) % n_players, (1 - shift) % n_players  # sièges de base[0] et base[1]
                ref_seat, cand_seat = (second, first) if swapped else (first, second)
                if rounds == 1:
                    profits = play_round(bots, seed=deal_seed, duration=duration, single_quote=single_quote).profits
                else:
                    profits = [p / rounds for p in
                               play_match(bots, seed=deal_seed, rounds=rounds, duration=duration,
                                          single_quote=single_quote).profits]
                gaps.append(profits[ref_seat] - profits[cand_seat])
        per_deal.append(sum(gaps) / len(gaps))
    return per_deal


def zoo_report(candidate, n_deals, n_players=4, seed=0, duration=240.0, log_file=None):
    """Pour chaque adversaire du zoo, sauf le candidat lui-même : (moyenne, borne basse, borne haute) du gain par manche."""
    return {
        name: mean_ci(duplicate_match(candidate, opp, n_deals, n_players, seed, duration, log_file))
        for name, opp in ZOO.items() if opp is not candidate
    }


GATE_REFERENCES = ("heuristique", "sniper", "bayesien", "marginal")  # bayesien : phases 0-1, marginal : phase 2


def minority_report(candidate, n_deals, n_players=4, seed=0, duration=240.0, references=GATE_REFERENCES):
    """Test de minorité : chaque référence, seule face à des copies du candidat. (moyenne, IC) du gain de la référence."""
    return {
        name: mean_ci(duplicate_match(CANDIDATES[name], candidate, n_deals, n_players, seed, duration))
        for name in references if CANDIDATES[name] is not candidate
    }


def gate(report, minority=None, mixed=None):
    """Règle d'entrée : un bot est refusé s'il ne bat pas nettement chaque référence (IC entièrement au-dessus de 0).
    Une référence absente du rapport (parce que c'est elle le candidat) est ignorée ; None s'il n'en reste aucune.

    `minority` (phase 4) : le gain de chaque référence seule face à des copies du candidat. Si l'une
    d'elles gagne nettement (IC entièrement au-dessus de 0), le candidat est refusé : il se fait
    exploiter quand il est nombreux à la table.
    `mixed` (phase 5i) : à une table référence + candidat + Hard simulés, l'écart de gain référence - candidat.
    Si l'un est nettement au-dessus de 0, le candidat est refusé. Contrairement au test de minorité, les copies
    du candidat ne s'y disputent pas la majorité entre elles."""
    if any(low > 0 for _mean, low, _high in [*(minority or {}).values(), *(mixed or {}).values()]):
        return False  # exploité
    refs = [name for name in GATE_REFERENCES if name in report]
    if not refs:
        return None
    return all(report[name][1] > 0 for name in refs)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--candidate", default="bayesien", choices=sorted(CANDIDATES))
    parser.add_argument("--deals", type=int, default=300)
    parser.add_argument("--players", type=int, default=4, choices=(4, 5))
    parser.add_argument("--duration", type=float, default=240.0, help="durée d'une manche en secondes")
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--logs", help="fichier JSONL où écrire le journal de chaque manche")
    parser.add_argument("--minority", action="store_true", help="ajouter le test de minorité à la règle d'entrée")
    parser.add_argument("--opponents", help="table mixte précise (noms séparés par des virgules) au lieu du zoo")
    parser.add_argument("--rounds", type=int, default=1, help="manches par partie (avec --opponents)")
    parser.add_argument("--out", help="fichier JSON où écrire le rapport")
    args = parser.parse_args()
    if args.deals < 2:
        parser.error("--deals doit valoir au moins 2 (il faut 2 valeurs pour un intervalle de confiance)")

    if args.opponents:  # une seule table mixte, éventuellement sur plusieurs manches
        names = [name.strip() for name in args.opponents.split(",")]
        unknown = [name for name in names if name not in CANDIDATES]
        if unknown:
            parser.error(f"adversaires inconnus : {', '.join(unknown)} (choix : {', '.join(sorted(CANDIDATES))})")
        if len(names) not in (3, 4):
            parser.error("--opponents : 3 ou 4 adversaires (Figgie se joue à 4 ou 5)")
        if args.minority:
            parser.error("--minority ne s'applique qu'au rapport contre le zoo, pas à une table mixte")
        log_file = open(args.logs, "w") if args.logs else None
        try:
            values = duplicate_match(CANDIDATES[args.candidate], [CANDIDATES[n] for n in names], args.deals,
                                     seed=args.seed, duration=args.duration, rounds=args.rounds, log_file=log_file)
        finally:
            if log_file:
                log_file.close()
        mean, low, high = mean_ci(values)
        print(f"{args.candidate} face à {args.opponents} ({args.rounds} manche(s) par partie, {args.deals} donnes) : "
              f"{mean:+.2f} $/manche [{low:+.2f} ; {high:+.2f}]")
        if args.out:
            with open(args.out, "w") as f:
                json.dump({"args": vars(args), "result": [mean, low, high]}, f, indent=2)
        return

    log_file = open(args.logs, "w") if args.logs else None
    try:
        report = zoo_report(CANDIDATES[args.candidate], args.deals, args.players, args.seed, args.duration, log_file)
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
    minority = None
    if args.minority:
        minority = minority_report(CANDIDATES[args.candidate], args.deals, args.players, args.seed, args.duration)
        print("\nTest de minorité (gain de la référence seule face aux copies du candidat) :")
        for name, (mean, low, high) in minority.items():
            print(f"| {name} seul | {mean:+.2f} | [{low:+.2f} ; {high:+.2f}] |")
    verdict = gate(report, minority)
    refs = [name for name in GATE_REFERENCES if name in report]
    print(f"Porte (bat {' et '.join(refs) or 'les références'}) :", "sans objet" if verdict is None else "ACCEPTÉ" if verdict else "REFUSÉ")
    if args.out:
        with open(args.out, "w") as f:
            json.dump({"args": vars(args), "report": report, "minority": minority, "worst": worst, "gate": verdict}, f, indent=2)


if __name__ == "__main__":
    main()
