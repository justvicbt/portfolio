"""Apprendre ce que le marché dit de la couleur objectif, puis vérifier que ça aide.

1. On joue des manches à des tables mixtes tirées au hasard dans le zoo (graines d'apprentissage).
2. On compte les événements par type et par place de leur couleur (objectif, jumelle, autre).
3. Sur d'autres manches (graines de validation), on mesure à plusieurs instants de la manche si
   la probabilité qu'utilise le lecteur (comptage des cartes x lecture du marché) est meilleure
   qu'avec le comptage seul. On choisit l'atténuation (`temper`) et la variante (lire aussi les
   échanges, ou seulement les cotations, puisque le comptage lit déjà les échanges) qui donnent
   les meilleures probabilités.

Aucune de ces graines ne sert aux tournois (graine 1) ni au réglage de la phase 2 (graine 2).

Usage : python3 -m figgie.learn --train 4000 --valid 1000            (phase 3)
        python3 -m figgie.learn --train 4000 --valid 1000 --league   (phase 4, la ligue)
        python3 -m figgie.learn --site --train 2400 --valid 600       (phase 5d, le marché du site)

Phase 5d (--site) : des manches jouées avec la règle du site, à des tables de Hard simulés plus un
autre joueur, comme les vraies manches de Rasmus Suonio (trois bots Hard et son bot). Le modèle lit
les cotations par fenêtre de temps, avec le consensus de la table (signals.TimedSignalModel).
Les vraies manches ne servent jamais à apprendre : elles servent de test (figgie.reel --calibration).

Phase 5s, --hard : les mêmes tables, avec un autre Hard simulé à la place de celui de la phase 5c :
        python3 -m figgie.learn --site --hard hard_simule_v3 --train 2400 --valid 600 --out modeles/signaux_site_v3.json
"""
import argparse
import json
import math
import random
from multiprocessing import Pool
from pathlib import Path

from figgie.bots import ABNORMAL, MODEL_PATH, MODELS_DIR, ZOO
from figgie.engine import play_round
from figgie.bots import UNIFORM
from figgie.signals import ALL_KINDS, MarketReading, SignalModel, TimedSignalModel, events_from_log
from figgie.valuation import goal_probabilities, known_minimums

TRAIN_SEED, VALID_SEED = 3, 4
LEAGUE_TRAIN_SEED, LEAGUE_VALID_SEED = 7, 8
CHECKPOINTS = (5, 15, 30, 60, 120, 240)  # secondes
TEMPERS = (0.0, 0.05, 0.1, 0.2, 0.3, 0.5, 0.7, 1.0)
LEARNERS = [name for name in ZOO if name != "lecteur"]  # phase 3 : le lecteur n'apprend pas sur lui-même
# Phase 4, la ligue : on apprend aussi sur des parties où jouent des lecteurs et des menteurs,
# pour que le modèle corresponde aux tables où le lecteur se faisait exploiter.
LEAGUE = list(ZOO) + ["menteur"]
POOL = {**ZOO, **ABNORMAL}


def _play(job):
    """Une manche à une table mixte : renvoie (main initiale du siège 0, événements, objectif)."""
    i, base, names = job
    seed = base * 1_000_000 + i
    rng = random.Random(seed)
    n = rng.choice((4, 5))
    bots = [POOL[rng.choice(names)] for _ in range(n)]
    log = play_round(bots, seed=seed).log
    return log["hands"][0], events_from_log(log), log["goal"]


def play_rounds(n, base, names=LEARNERS):
    with Pool() as pool:
        return pool.map(_play, [(i, base, names) for i in range(n)], chunksize=20)


def state_at(hand, events, t):
    """Ce que sait le siège 0 à l'instant t : sa main, les cartes connues des autres, les événements vus."""
    seen = [e for e in events if e[0] <= t]
    hand = dict(hand)
    trades = []
    for e, nxt in zip(seen, seen[1:]):
        if e[2] == "bought" and nxt[2] == "sold":  # un échange = deux événements consécutifs
            trades.append((e[1], nxt[1], e[3], e[4]))
            hand[e[3]] += (e[1] == 0) - (nxt[1] == 0)
    return hand, trades, seen


def reader_posterior(model, temper, hand0, events, t):
    """La probabilité qu'utilise le lecteur : comptage des cartes x lecture du marché."""
    hand, trades, seen = state_at(hand0, events, t)
    n_players = 40 // sum(hand0.values())
    mins = known_minimums(trades, n_players)
    market = model.posterior(UNIFORM, seen, temper=temper, me=0)
    return goal_probabilities(hand, mins, 0, goal_weights=market, drawn=hand0)  # comme le lecteur : comptage corrigé


def score_posteriors(model, rounds, temper):
    """Pour chaque instant : (taux de bonne réponse, log-score moyen) du point de vue du siège 0.
    Log-score = log de la probabilité donnée à la vraie couleur : plus c'est haut, mieux c'est."""
    out = {}
    for t in CHECKPOINTS:
        hits, logscore = 0, 0.0
        for hand, events, goal in rounds:
            post = reader_posterior(model, temper, hand, events, t)
            hits += max(post, key=post.get) == goal
            logscore += math.log(max(post[goal], 1e-12))
        out[t] = (hits / len(rounds), logscore / len(rounds))
    return out


def calibration(model, rounds, temper, t=60):
    """Quand le modèle annonce p, la couleur est-elle l'objectif une fois sur p ? Par tranches de 10 %."""
    bins = {}
    for hand, events, goal in rounds:
        for suit, p in reader_posterior(model, temper, hand, events, t).items():
            b = min(9, int(p * 10))
            n, k = bins.get(b, (0, 0))
            bins[b] = (n + 1, k + (suit == goal))
    return {f"{b * 10}-{b * 10 + 10} %": (n, k / n) for b, (n, k) in sorted(bins.items())}


VARIANTS = {"cotations et échanges": ALL_KINDS, "cotations seules": ("bid", "ask")}

# --- Phase 5d : le marché du site ---------------------------------------------------------------

SITE_TRAIN_SEED, SITE_VALID_SEED = 51, 52
SITE_SEATMATES = ("marginal", "adaptatif_v3", "lecteur", "bayesien", "hard_simule", "heuristique")
SITE_TEMPERS = (0.05, 0.1, 0.2, 0.3, 0.5, 0.7, 1.0)


def site_table(i, base, hard="hard_simule"):
    """La i-ième table : sa graine et ses joueurs, des Hard simulés (`hard`) et un autre joueur à une place tirée au
    hasard. Phase 5s : changer de Hard garde les mêmes tailles de table et le même voisin, à la même place."""
    seed = base * 1_000_000 + i
    rng = random.Random(seed)
    n = rng.choice((4, 5))
    names = [hard] * (n - 1) + [rng.choice(SITE_SEATMATES)]
    rng.shuffle(names)  # la permutation ne dépend pas des noms : le voisin reste à sa place quel que soit `hard`
    return seed, names


def _play_site(job):
    """Une manche avec la règle du site, à la table site_table(i, base, hard).
    Renvoie (main initiale du siège 0, événements, objectif, durée, nombre de joueurs)."""
    from figgie.evaluate import CANDIDATES
    seed, names = site_table(*job)
    result = play_round([CANDIDATES[x] for x in names], seed=seed, single_quote=True)
    return result.log["hands"][0], result.events, result.log["goal"], result.log["duration"], len(names)


def site_rounds(n, base, hard="hard_simule"):
    with Pool() as pool:
        return pool.map(_play_site, [(i, base, hard) for i in range(n)], chunksize=10)


def site_posterior(model, temper, hand0, events, t, duration, n, weights=None):
    """La probabilité qu'utilise le lecteur du site, vue du siège 0 à l'instant t."""
    hand, trades, seen = state_at(hand0, events, t)
    reading = MarketReading(model, temper, duration, 0, range(n), weights)
    reading.update(seen)
    return goal_probabilities(hand, known_minimums(trades, n), 0, goal_weights=reading.posterior(UNIFORM, t),
                              drawn=hand0)


def score_site(model, rounds, temper):
    """Comme score_posteriors, pour le lecteur du site : {instant: (taux de bonne réponse, log-score moyen)}."""
    out = {}
    for t in CHECKPOINTS:
        posts = [(site_posterior(model, temper, hand, events, t, d, n), goal) for hand, events, goal, d, n in rounds]
        out[t] = (sum(max(p, key=p.get) == g for p, g in posts) / len(posts),
                  sum(math.log(max(p[g], 1e-12)) for p, g in posts) / len(posts))
    return out


def learn_site(args):
    train, valid = site_rounds(args.train, SITE_TRAIN_SEED, args.hard), site_rounds(args.valid, SITE_VALID_SEED, args.hard)
    model = TimedSignalModel.fit_rounds([(ev, goal, d, n) for _h, ev, goal, d, n in train])
    results = {temper: score_site(model, valid, temper) for temper in SITE_TEMPERS}
    print("| atténuation | " + " | ".join(f"{t} s" for t in CHECKPOINTS) + " |")
    print("|---" * (len(CHECKPOINTS) + 1) + "|")
    for temper, by_t in results.items():
        print(f"| {temper} | " + " | ".join(f"{acc:.1%} ({ls:+.3f})" for acc, ls in by_t.values()) + " |")
    temper = max(results, key=lambda tp: sum(ls for _acc, ls in results[tp].values()))
    print(f"\nRetenu : atténuation {temper} (meilleur log-score moyen sur {args.valid} manches de validation simulées)")
    out = Path(args.out or MODELS_DIR / "signaux_site.json")
    out.write_text(json.dumps({**model.to_dict(), "temper": temper}, indent=1))
    print(f"Modèle écrit dans {out}")
    if args.report:
        Path(args.report).write_text(json.dumps({"args": vars(args), "temper": temper, "results": {
            str(tp): {str(t): x for t, x in by_t.items()} for tp, by_t in results.items()}}, indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--train", type=int, default=4000)
    parser.add_argument("--valid", type=int, default=1000)
    parser.add_argument("--league", action="store_true", help="apprendre sur les tables de la ligue (phase 4)")
    parser.add_argument("--out")
    parser.add_argument("--report", help="fichier JSON où écrire les mesures de validation")
    parser.add_argument("--site", action="store_true", help="phase 5d : apprendre sur le marché du site")
    parser.add_argument("--hard", default="hard_simule", help="phase 5s : le Hard simulé des tables du site")
    args = parser.parse_args()
    if args.site:
        return learn_site(args)

    if args.league:
        train = play_rounds(args.train, LEAGUE_TRAIN_SEED, LEAGUE)
        valid = play_rounds(args.valid, LEAGUE_VALID_SEED, LEAGUE)
        args.out = args.out or str(MODELS_DIR / "signaux_ligue.json")
    else:
        train = play_rounds(args.train, TRAIN_SEED)
        valid = play_rounds(args.valid, VALID_SEED)
        args.out = args.out or str(MODEL_PATH)
    best = None  # (log-score total, variante, atténuation, modèle)
    report = {}
    for variant, kinds in VARIANTS.items():
        model = SignalModel.fit(((events, goal) for _hand, events, goal in train), kinds=kinds)
        results = {temper: score_posteriors(model, valid, temper) for temper in TEMPERS}
        report[variant] = results
        print(f"\n{variant}\n")
        print("| atténuation | " + " | ".join(f"{t} s" for t in CHECKPOINTS) + " |")
        print("|---" * (len(CHECKPOINTS) + 1) + "|")
        for temper, by_t in results.items():
            cells = " | ".join(f"{acc:.1%} ({ls:+.3f})" for acc, ls in by_t.values())
            print(f"| {'cartes seules' if temper == 0 else temper} | {cells} |")
            total = sum(ls for _acc, ls in by_t.values())
            if best is None or total > best[0]:
                best = (total, variant, temper, model)
    _, variant, temper, model = best
    calib = calibration(model, valid, temper)
    print(f"\nRetenu : {variant}, atténuation {temper} (meilleur log-score moyen)")
    print("Calibration à 60 s : " + ", ".join(f"{k} -> {f:.0%} (n={n})" for k, (n, f) in calib.items()))
    best = temper
    results = report

    data = model.to_dict()
    data["temper"] = best
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(data, indent=1))
    print(f"Modèle écrit dans {args.out}")
    if args.report:
        Path(args.report).write_text(json.dumps(
            {"args": vars(args), "variant": variant, "temper": best, "calibration_60s": calib,
             "results": {v: {str(tp): {str(t): x for t, x in by_t.items()} for tp, by_t in res.items()}
                         for v, res in results.items()}}, indent=2))


if __name__ == "__main__":
    main()
