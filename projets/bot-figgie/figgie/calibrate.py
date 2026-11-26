"""Phase 5c : régler le Hard simulé pour que son marché ressemble à celui de figgie.com.

On compare les mesures de figgie.reel.market_stats sur les 60 vraies manches de Rasmus Suonio et sur
des tables de 4 Hard simulés, jouées avec la règle du site. Les vraies manches ont 3 bots Hard et le
bot de Rasmus : on ne mesure que les bots Hard, et les échanges sont comptés par paire de bots Hard.

    python3 -m figgie.calibrate --settings 300 --rounds 20 --out resultats/phase5c/calibration_hard.json

Phase 5j, --lift : on compare aussi la part des offres de vente d'un bot Hard qu'un autre prend, par tranche de prix
(figgie.reel.lift_rates). Le Hard de la phase 5c en prenait bien trop au-dessus de 7 $ dans les couleurs hors objectif.

Phase 5q, --consensus : on compare aussi la part des manches où le consensus des bots Hard met l'objectif en tête, à
120, 180 et 239 s (figgie.reel.consensus_hits), et la force de lecture `read` peut monter plus haut. Sur les vraies
manches, ce consensus trouve l'objectif à la cloche dans 91 % des manches, entre les Hard recalés dans 67 % (phase 5p).

Phase 5r, --hint : on règle le Hard v3 (bots.HardBotV3), qui reçoit un indice privé sur l'objectif, avec en plus
l'instant où l'indice devient sûr (hint_time) et sa forme (hint_power).
"""
import argparse
import json
import random
from multiprocessing import Pool
from pathlib import Path

from figgie.bots import HardBot, HardBotV3
from figgie.engine import play_round
from figgie.exploit import _map, sample_settings
from figgie.reel import consensus_hits, lift_rates, load_rasmus, market_stats, simulated_round

SPACE = {
    "base": [0, 1, 2, 3, 4, 5],
    "goal_worth": [8, 12, 16, 20, 25, 30, 40, 50],
    "margin": [1, 2, 3, 4, 6, 8],
    "margin_power": [0.5, 1, 2, 3],
    "pace": [0.6, 0.8, 1.0, 1.3, 1.6, 2.0],
    "noise": [0, 1, 2, 3, 4, 6, 8, 10],
    "open_ask": [15, 20, 25, 30],
    "read": [0, 0.05, 0.1, 0.15, 0.2, 0.3, 0.4],
}
SEARCH_SEED, CHECK_SEED = 31, 32
# Mesures comparées, et l'écart qui compte pour une unité d'erreur
# (l'objectif compte double : c'est ce qui sépare un bot qui lit le marché d'un bot qui cote au hasard)
SCALES = {"hard_trades_per_pair": 2.0, "quotes_per_min": 8.0, "first_quote": 2.0, "goal_price": 1.0,
          "other_price": 1.0, "goal_top_bid": 1.0, "other_top_bid": 1.0}
MINUTE_SCALE = 0.1  # pour la répartition des échanges par minute, somme des écarts
LIFT_SCALE = 0.05  # phase 5j : 5 points de part d'offres prises = une unité d'erreur
CONSENSUS_SCALE = 0.05  # phase 5q : 5 points de manches où le consensus désigne l'objectif = une unité d'erreur
CONSENSUS_READ = [0.6, 0.8, 1.2]  # phase 5q : forces de lecture ajoutées à SPACE avec --consensus
HINT_SPACE = {"hint_time": [60, 120, 180, 240, 300, 400], "hint_power": [0.5, 1, 2, 3]}  # phase 5r, avec --hint


def hard_bot(params, hint=False):
    return type("CalibratedHard", (HardBotV3 if hint else HardBot,), dict(params))


def distance(sim, real, lift=False, consensus=False):
    """Écart entre deux jeux de mesures : somme des carrés des écarts, chacun ramené à son échelle.
    Infini si une mesure manque (aucun échange entre bots simulés, par exemple).
    `lift` (phase 5j) : ajoute les parts d'offres de vente prises, par tranche de prix.
    `consensus` (phase 5q) : ajoute la part des manches où le consensus des bots Hard désigne l'objectif."""
    if any(sim[k] is None for k in SCALES) or (lift and any(v is None for v in sim["lift"].values())):
        return float("inf")
    total = sum(((sim[k] - real[k]) / scale) ** 2 for k, scale in SCALES.items())
    if lift:
        total += sum(((sim["lift"][k] - real["lift"][k]) / LIFT_SCALE) ** 2 for k in real["lift"])
    if consensus:
        total += sum(((a - b) / CONSENSUS_SCALE) ** 2 for a, b in zip(sim["consensus"], real["consensus"]))
    return total + (sum(abs(a - b) for a, b in zip(sim["by_minute"], real["by_minute"])) / MINUTE_SCALE) ** 2


def measures(rounds):
    return {**market_stats(rounds), "lift": lift_rates(rounds), "consensus": consensus_hits(rounds)}


def simulate(params, rounds, seed, players=4, hint=False):
    bot = hard_bot(params, hint)
    return measures([simulated_round(play_round([bot] * players, seed=seed * 1_000_000 + g, single_quote=True))
                     for g in range(rounds)])


def _score(job):
    params, rounds, seed, real, lift, consensus, hint = job
    return distance(simulate(params, rounds, seed, hint=hint), real, lift, consensus), params


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--settings", type=int, default=300, help="réglages tirés au hasard")
    parser.add_argument("--rounds", type=int, default=20, help="manches simulées par réglage")
    parser.add_argument("--keep", type=int, default=5, help="meilleurs réglages revérifiés sur d'autres donnes")
    parser.add_argument("--out", help="fichier JSON des résultats")
    parser.add_argument("--lift", action="store_true", help="phase 5j : compter aussi les parts d'offres de vente prises")
    parser.add_argument("--consensus", action="store_true",
                        help="phase 5q : compter aussi la part des manches où le consensus des Hard désigne l'objectif")
    parser.add_argument("--hint", action="store_true", help="phase 5r : régler le Hard v3, avec son indice privé")
    args = parser.parse_args()
    real = measures(load_rasmus())
    space = {**SPACE, "read": SPACE["read"] + CONSENSUS_READ} if args.consensus else SPACE
    if args.hint:
        space = {**space, **HINT_SPACE}
    settings = sample_settings(space, args.settings, random.Random(SEARCH_SEED))
    with Pool() as pool:
        scored = sorted(_map(pool, _score, [(p, args.rounds, SEARCH_SEED, real, args.lift, args.consensus, args.hint) for p in settings], "recherche"), key=lambda x: x[0])
        best = [p for _d, p in scored[:args.keep]]
        checked = sorted(_map(pool, _score, [(p, 3 * args.rounds, CHECK_SEED, real, args.lift, args.consensus, args.hint) for p in best], "revérification"), key=lambda x: x[0])
    final = checked[0][1]
    stats = simulate(final, 3 * args.rounds, CHECK_SEED, hint=args.hint)
    fmt = lambda v: "-" if v is None else "/".join(f"{x:.2f}" for x in v) if isinstance(v, list) else f"{v:.2f}"
    print(f"{len(settings)} réglages sur {args.rounds} manches (graine {SEARCH_SEED}), "
          f"les {args.keep} meilleurs revérifiés sur {3 * args.rounds} autres (graine {CHECK_SEED}).")
    for d, p in checked:
        print(f"  écart {d:7.2f}  {p}")
    print(f"Retenu : {final}")
    print(f"{'mesure':22s} {'figgie.com':>12s} {'Hard simulé':>12s}")
    for k in ["trades", "hard_trades_per_pair", "by_minute", "quotes_per_min", "first_quote", "goal_price",
              "other_price", "goal_top_bid", "other_top_bid"]:
        print(f"{k:22s} {fmt(real[k]):>12s} {fmt(stats[k]):>12s}")
    for k in real["lift"]:
        print(f"{'prise ' + k:22s} {fmt(real['lift'][k]):>12s} {fmt(stats['lift'][k]):>12s}")
    print(f"{'consensus 120/180/239':22s} {fmt(real['consensus']):>12s} {fmt(stats['consensus']):>12s}")
    if args.out:
        Path(args.out).write_text(json.dumps({"args": vars(args), "real": real, "search": scored, "checked": checked,
                                              "final": final, "final_stats": stats}, indent=1))


if __name__ == "__main__":
    main()
