"""Phase 5c : régler le Hard simulé pour que son marché ressemble à celui de figgie.com.

On compare les mesures de figgie.reel.market_stats sur les 60 vraies manches de Rasmus Suonio et sur
des tables de 4 Hard simulés, jouées avec la règle du site. Les vraies manches ont 3 bots Hard et le
bot de Rasmus : on ne mesure que les bots Hard, et les échanges sont comptés par paire de bots Hard.

    python3 -m figgie.calibrate --settings 300 --rounds 20 --out resultats/phase5c/calibration_hard.json
"""
import argparse
import json
import random
from multiprocessing import Pool
from pathlib import Path

from figgie.bots import HardBot
from figgie.engine import play_round
from figgie.exploit import sample_settings
from figgie.reel import load_rasmus, market_stats, simulated_round

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


def hard_bot(params):
    return type("CalibratedHard", (HardBot,), dict(params))


def distance(sim, real):
    """Écart entre deux jeux de mesures : somme des carrés des écarts, chacun ramené à son échelle.
    Infini si une mesure manque (aucun échange entre bots simulés, par exemple)."""
    if any(sim[k] is None for k in SCALES):
        return float("inf")
    total = sum(((sim[k] - real[k]) / scale) ** 2 for k, scale in SCALES.items())
    return total + (sum(abs(a - b) for a, b in zip(sim["by_minute"], real["by_minute"])) / MINUTE_SCALE) ** 2


def simulate(params, rounds, seed, players=4):
    bot = hard_bot(params)
    return market_stats([simulated_round(play_round([bot] * players, seed=seed * 1_000_000 + g, single_quote=True))
                         for g in range(rounds)])


def _score(job):
    params, rounds, seed, real = job
    return distance(simulate(params, rounds, seed), real), params


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--settings", type=int, default=300, help="réglages tirés au hasard")
    parser.add_argument("--rounds", type=int, default=20, help="manches simulées par réglage")
    parser.add_argument("--keep", type=int, default=5, help="meilleurs réglages revérifiés sur d'autres donnes")
    parser.add_argument("--out", help="fichier JSON des résultats")
    args = parser.parse_args()
    real = market_stats(load_rasmus())
    settings = sample_settings(SPACE, args.settings, random.Random(SEARCH_SEED))
    with Pool() as pool:
        scored = sorted(pool.map(_score, [(p, args.rounds, SEARCH_SEED, real) for p in settings]), key=lambda x: x[0])
        best = [p for _d, p in scored[:args.keep]]
        checked = sorted(pool.map(_score, [(p, 3 * args.rounds, CHECK_SEED, real) for p in best]), key=lambda x: x[0])
    final = checked[0][1]
    stats = simulate(final, 3 * args.rounds, CHECK_SEED)
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
    if args.out:
        Path(args.out).write_text(json.dumps({"args": vars(args), "real": real, "search": scored, "checked": checked,
                                              "final": final, "final_stats": stats}, indent=1))


if __name__ == "__main__":
    main()
