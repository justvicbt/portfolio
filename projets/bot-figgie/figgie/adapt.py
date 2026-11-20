"""Phase 5 : reconnaître la table et choisir son réglage en conséquence.

Un bandit qui apprendrait sur ses gains ne peut rien distinguer en une partie : le gain d'une
manche varie d'environ 65 $ d'une donne à l'autre, alors que deux réglages ne diffèrent que de
quelques dollars. On apprend donc hors ligne, en simulation et en donnes dupliquées (sans bruit
de donne), quel réglage marche contre quel type de table. En partie, le bot mesure le comportement
des autres, qui est peu bruité, retrouve les tables d'entraînement qui ressemblent le plus à la
sienne (plus proches voisins) et prend le réglage qui y marchait le mieux.

Usage : python3 -m figgie.adapt --tables 80 --deals 100
"""
import argparse
import json
import math
import random
import statistics
from multiprocessing import Pool
from pathlib import Path

from figgie.bots import ABNORMAL, MODELS_DIR, ZOO, MarginalBot, load_model
from figgie.engine import play_round

ARMS = [(6, 3), (8, 1), (10, 3), (12, 3)]  # (spread, marge) possibles ; (8, 1) est le réglage du marginal
DEFAULT_ARM = (8, 1)
K = 5  # nombre de tables voisines consultées
PROFILE_ROUNDS = 10  # manches jouées pour mesurer le profil d'une table d'entraînement
MISSING = {"spread": 20.0, "latency": 10.0}  # valeurs prises quand personne ne cote des deux côtés, ou ne recote


def arm_key(arm):
    return f"{arm[0]},{arm[1]}"


def parse_arm(key):
    spread, edge = key.split(",")
    return int(spread), int(edge)


def table_profile(events, me, duration, n_players=None):
    """Le comportement des autres joueurs pendant une manche, mesuré sur le fil public.

    Pour chaque adversaire : combien il cote par minute, l'écart entre ses prix d'achat et de vente
    quand il cote des deux côtés d'une couleur, et le temps qu'il met à recoter après un échange
    (le carnet est alors vide). On résume ensuite la table en quelques nombres.
    """
    players = range(n_players) if n_players else sorted({e[1] for e in events} | {me})
    opponents = [j for j in players if j != me]
    quotes = {j: 0 for j in opponents}
    spreads = {j: [] for j in opponents}
    delays = {j: [] for j in opponents}
    book, waiting, last_trade = {}, set(), None
    for t, player, kind, suit, price in sorted(events, key=lambda e: e[0]):
        if kind in ("bought", "sold"):
            book.clear()  # après un échange, toutes les cotations sont annulées
            last_trade, waiting = t, set(opponents)
            continue
        if kind == "cancel":
            book.pop((player, suit), None)  # ses cotations de cette couleur ont disparu
            continue
        if player == me or player not in quotes:
            continue
        quotes[player] += 1
        side = book.setdefault((player, suit), {})
        side[kind] = price
        if "bid" in side and "ask" in side:
            spreads[player].append(side["ask"] - side["bid"])
        if player in waiting:
            delays[player].append(t - last_trade)
            waiting.discard(player)
    rates = [quotes[j] / duration * 60 for j in opponents]
    mean_spreads = [statistics.fmean(spreads[j]) for j in opponents if spreads[j]] or [MISSING["spread"]]
    latencies = [statistics.median(delays[j]) for j in opponents if delays[j]] or [MISSING["latency"]]
    return {
        "quote_rate_mean": statistics.fmean(rates),
        "quote_rate_max": max(rates),
        "spread_min": min(mean_spreads),
        "spread_median": statistics.median(mean_spreads),
        "latency_min": min(latencies),
        "silent_share": sum(q == 0 for q in quotes.values()) / len(opponents),
    }


def mean_profile(profiles):
    return {k: statistics.fmean(p[k] for p in profiles) for k in profiles[0]}


class Neighbors:
    """Plus proches voisins : `training` = [(profil de table, {réglage: gain moyen})]."""

    def __init__(self, training):
        self.training = [(dict(f), dict(a)) for f, a in training]
        self.keys = sorted(self.training[0][0])
        self.scale = {}
        for k in self.keys:
            values = [f[k] for f, _ in self.training]
            sd = statistics.pstdev(values) if len(values) > 1 else 0.0
            self.scale[k] = sd or 1.0  # chaque mesure ramenée à son écart-type, pour qu'aucune n'écrase les autres

    def nearest(self, features, k=K):
        def distance(f):
            return math.sqrt(sum(((f[key] - features[key]) / self.scale[key]) ** 2 for key in self.keys))
        return sorted(self.training, key=lambda item: distance(item[0]))[:k]

    def best(self, features, k=K):
        """Le réglage qui rapportait le plus, en moyenne, sur les `k` tables les plus ressemblantes."""
        return self.best_many([features], k)

    def best_many(self, profiles, k=K):
        """Comme best, mais avec plusieurs profils (un par manche déjà jouée) : on réunit leurs voisins."""
        neighbors = [item for f in profiles for item in self.nearest(f, k)]
        arms = neighbors[0][1].keys()
        return max(arms, key=lambda a: statistics.fmean(gains[a] for _, gains in neighbors))

    def to_dict(self):
        return {"training": [[f, a] for f, a in self.training]}

    @classmethod
    def from_dict(cls, data):
        return cls([(f, a) for f, a in data["training"]])


class AdaptiveBot(MarginalBot):
    """Le marginal, qui choisit son réglage (spread, marge) au début de chaque manche d'après ce qu'il
    a vu de la table aux manches précédentes. Première manche : le réglage du marginal."""
    name = "adaptatif"
    model_file = "adaptation.json"

    @classmethod
    def neighbors(cls):
        return load_model(cls.model_file, Neighbors.from_dict, "figgie.adapt")

    def __init__(self):
        super().__init__()
        self.memory = {}  # remplacée par la mémoire de la partie (play_match)
        self._feed, self._arm, self._duration, self._n = [], None, 240.0, None

    def choose(self, profiles):
        """Version 1 : le profil moyen des manches passées, comparé aux profils moyens des tables d'entraînement."""
        return parse_arm(self.neighbors().best(mean_profile(profiles)))

    def act(self, view, rng):
        if self._arm is None:  # début de manche : on fixe le réglage pour toute la manche
            profiles = self.memory.get("profiles", [])
            self._arm = self.choose(profiles) if profiles else DEFAULT_ARM
            self.spread, self.edge = self._arm
            self.memory.setdefault("arms", []).append(self._arm)
            self._duration, self._n = view.duration, view.n_players
        self._feed = view.events
        return super().act(view, rng)

    def end_round(self, reveal):
        profile = table_profile(self._feed, reveal["seat"], self._duration, self._n)
        self.memory.setdefault("profiles", []).append(profile)


class AdaptiveV2Bot(AdaptiveBot):
    """Version 2, après la relecture du code. La version 1 comparait le profil moyen de la partie à des
    profils d'entraînement moyennés sur 10 manches et mesurés avec le seul réglage de référence. En
    partie, le bot mesure pourtant une manche à la fois, avec le réglage qu'il a choisi, qui change
    lui-même le comportement de la table. La version 2 apprend sur des profils d'une seule manche,
    mesurés avec chacun des réglages, et interroge les voisins manche par manche."""
    name = "adaptatif_v2"
    model_file = "adaptation_v2.json"

    def choose(self, profiles):
        return parse_arm(self.neighbors().best_many(profiles))


# --- Apprentissage hors ligne -------------------------------------------------------------------

TRAIN_SEED, VALID_SEED = 9, 10
POOL = {**ZOO, "menteur": ABNORMAL["menteur"]}
# Des tables tirées dans la ligue, avec une part de tables pleines de marginaux : ce sont celles
# où les copies se font concurrence, le cas que le test de minorité punit.
CHOICES = list(POOL) + ["marginal"] * 4


def arm_bot(arm):
    return type("Arm", (MarginalBot,), {"spread": arm[0], "edge": arm[1]})


def table_opponents(i, base):
    """La table d'entraînement numéro i : sa graine et ses adversaires (toujours les mêmes pour i et base)."""
    seed = base * 1000 + i  # donnes : seed x 1 000 000 + d, loin des graines des autres expériences
    rng = random.Random(seed)
    n = rng.choice((4, 5))
    return seed, [POOL[rng.choice(CHOICES)] for _ in range(n - 1)]


def _profiles_by_arm(job):
    """Version 2 : pour une table, 10 profils d'une manche chacun, mesurés avec chacun des réglages."""
    i, base = job
    seed, opponents = table_opponents(i, base)
    out = {}
    for arm in ARMS:
        out[arm_key(arm)] = [
            table_profile(play_round([arm_bot(arm)] + opponents, seed=f"{seed}:profil2:{arm_key(arm)}:{r}").events,
                          0, 240.0, len(opponents) + 1)
            for r in range(PROFILE_ROUNDS)]
    return out


def build_v2(report_path, out):
    """Version 2, construite à partir des gains déjà mesurés pour la version 1 (rapport de figgie.adapt).

    Validation croisée sur les tables d'entraînement, dont on connaît le gain des 4 réglages : chaque
    table est retirée du modèle à tour de rôle, puis sert de test. On compare la version 1 telle
    qu'elle a été validée (profil moyen de 10 manches), la version 1 telle qu'elle joue vraiment
    (profil d'1 ou 3 manches) et la version 2 (1 ou 3 manches, interrogées une par une).
    """
    train = json.loads(Path(report_path).read_text())["train"]
    for i, (_f, _g, names) in enumerate(train):  # on vérifie qu'on a bien retrouvé les mêmes tables
        assert [o.name for o in table_opponents(i, TRAIN_SEED)[1]] == names, i
    with Pool() as pool:
        by_table = pool.map(_profiles_by_arm, [(i, TRAIN_SEED) for i in range(len(train))])
    default = arm_key(DEFAULT_ARM)
    scores = {name: [] for name in ("fixe", "v1, 10 manches", "v1, 1 manche", "v1, 3 manches",
                                    "v2, 1 manche", "v2, 3 manches", "meilleur")}
    for held, ((f, gains, _n), by_arm) in enumerate(zip(train, by_table)):
        others = [x for j, x in enumerate(zip(train, by_table)) if j != held]
        v1 = Neighbors([(tf, tg) for (tf, tg, _), _ in others])
        v2 = Neighbors([(p, tg) for (_, tg, _), arms in others for profiles in arms.values() for p in profiles])
        singles = by_arm[default]  # ce que le bot voit en partie : une manche à la fois, au réglage de départ
        scores["fixe"].append(gains[default])
        scores["v1, 10 manches"].append(gains[v1.best(f)])
        scores["v1, 1 manche"].append(gains[v1.best(singles[0])])
        scores["v1, 3 manches"].append(gains[v1.best(mean_profile(singles[:3]))])
        scores["v2, 1 manche"].append(gains[v2.best_many(singles[:1])])
        scores["v2, 3 manches"].append(gains[v2.best_many(singles[:3])])
        scores["meilleur"].append(max(gains.values()))
    model = Neighbors([(p, g) for (_, g, _), arms in zip(train, by_table) for profiles in arms.values() for p in profiles])
    Path(out).write_text(json.dumps(model.to_dict(), indent=1))
    return scores


def _table(job):
    """Pour une table d'entraînement : son profil (vu avec le réglage de référence) et le gain de chaque
    réglage, mesuré en donnes dupliquées sur les mêmes donnes pour tous les réglages."""
    from figgie.evaluate import duplicate_match  # import ici : evaluate importe déjà ce module
    i, base, deals = job
    seed, opponents = table_opponents(i, base)
    n = len(opponents) + 1
    gains = {arm_key(arm): statistics.fmean(duplicate_match(arm_bot(arm), opponents, deals, seed=seed))
             for arm in ARMS}
    profiles = []
    for r in range(PROFILE_ROUNDS):  # le profil, tel que le verrait le bot avec son réglage de départ
        result = play_round([arm_bot(DEFAULT_ARM)] + opponents, seed=f"{seed}:profil:{r}")
        profiles.append(table_profile(result.events, 0, result.log["duration"], n))
    return mean_profile(profiles), gains, [o.name for o in opponents]


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--tables", type=int, default=80)
    parser.add_argument("--valid", type=int, default=30)
    parser.add_argument("--deals", type=int, default=100, help="donnes par table et par réglage")
    parser.add_argument("--report", help="fichier JSON où écrire les mesures de validation")
    parser.add_argument("--out", default=str(MODELS_DIR / AdaptiveBot.model_file),
                        help="où écrire le modèle (par défaut, celui que charge le bot adaptatif)")
    parser.add_argument("--v2-from", help="construire la version 2 à partir du rapport (--report) de la version 1")
    args = parser.parse_args()
    if args.v2_from:
        from figgie.evaluate import mean_ci
        out = args.out if args.out != str(MODELS_DIR / AdaptiveBot.model_file) else str(MODELS_DIR / AdaptiveV2Bot.model_file)
        scores = build_v2(args.v2_from, out)
        fixed = scores["fixe"]
        print("Validation croisée sur les tables d'entraînement (gain moyen $/manche, écart au réglage fixe) :")
        for name, values in scores.items():
            diff = mean_ci([v - f for v, f in zip(values, fixed)])
            print(f"  {name:16s} {statistics.fmean(values):+6.2f}   écart {diff[0]:+.2f} [{diff[1]:+.2f} ; {diff[2]:+.2f}]")
        print(f"Modèle écrit dans {out}")
        if args.report:
            Path(args.report).write_text(json.dumps({"args": vars(args), "scores": scores}, indent=1))
        return
    if max(args.tables, args.valid) >= 1000:
        parser.error("au plus 999 tables : au-delà, les graines d'entraînement et de validation se chevauchent")

    with Pool() as pool:
        train = pool.map(_table, [(i, TRAIN_SEED, args.deals) for i in range(args.tables)])
        valid = pool.map(_table, [(i, VALID_SEED, args.deals) for i in range(args.valid)])
    model = Neighbors([(f, g) for f, g, _ in train])

    # Validation sur des tables jamais vues : gain du réglage choisi, comparé au réglage fixe et au meilleur possible.
    rows = []
    for f, gains, names in valid:
        chosen = model.best(f)
        rows.append({"table": names, "chosen": chosen, "gain_chosen": gains[chosen],
                     "gain_default": gains[arm_key(DEFAULT_ARM)], "gain_best": max(gains.values()),
                     "best": max(gains, key=gains.get)})
    mean = lambda key: statistics.fmean(r[key] for r in rows)
    print(f"Validation sur {len(rows)} tables jamais vues ({args.deals} donnes par réglage) :")
    print(f"  réglage fixe (8, 1)     {mean('gain_default'):+.2f} $/manche")
    print(f"  réglage choisi          {mean('gain_chosen'):+.2f} $/manche")
    print(f"  meilleur réglage connu  {mean('gain_best'):+.2f} $/manche (inaccessible : il faudrait connaître la réponse)")
    print("  réglages choisis : " + ", ".join(f"{a} x{sum(r['chosen'] == a for r in rows)}" for a in map(arm_key, ARMS)))
    print("  meilleurs réglages : " + ", ".join(f"{a} x{sum(r['best'] == a for r in rows)}" for a in map(arm_key, ARMS)))

    path = Path(args.out)
    path.write_text(json.dumps(model.to_dict(), indent=1))
    print(f"Modèle écrit dans {path}")
    if args.report:
        Path(args.report).write_text(json.dumps({"args": vars(args), "validation": rows,
                                                  "train": [[f, g, n] for f, g, n in train]}, indent=1))


if __name__ == "__main__":
    main()
