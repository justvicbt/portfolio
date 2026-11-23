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
import re
import statistics
from multiprocessing import Pool
from pathlib import Path

from figgie.bots import ABNORMAL, MODELS_DIR, ZOO, HardBot, MarginalBot, SiteReaderBot, load_model
from figgie.engine import SUITS, play_round
from figgie.valuation import goal_probabilities

ARMS = [(6, 3), (8, 1), (10, 3), (12, 3)]  # (spread, marge) possibles ; (8, 1) est le réglage du marginal
DEFAULT_ARM = (8, 1)
K = 5  # nombre de tables voisines consultées
PROFILE_ROUNDS = 10  # manches jouées pour mesurer le profil d'une table d'entraînement
MISSING = {"spread": 20.0, "latency": 10.0}  # valeurs prises quand personne ne cote des deux côtés, ou ne recote


def arm_key(arm):
    return ",".join(map(str, arm))


def parse_arm(key):
    """(spread, marge), ou en phase 5b (spread, marge, spread en fin de manche, marge en fin de manche)."""
    return tuple(int(x) for x in key.split(","))


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
    default_arm = DEFAULT_ARM

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
            self._arm = self.choose(profiles) if profiles else self.default_arm
            self.spread, self.edge, *late = self._arm
            if late:
                self.spread_late, self.edge_late = late
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


STRONG_HAND = 0.4  # au-delà, ma donne désigne une couleur objectif avec au moins 40 % de chances (23 % des mains)
DEFAULT_ARM_V3 = (8, 1, 8, 1)


def hand_strength(hand, n_players):
    """La plus forte probabilité de couleur objectif d'après ma seule donne (main concentrée ou plate)."""
    return max(goal_probabilities(hand, [dict.fromkeys(SUITS, 0)] * n_players, 0).values())


class AdaptiveV3Bot(AdaptiveV2Bot):
    """Phase 5b. Comme la version 2, avec deux différences. Elle a appris sur des tables où jouent aussi
    des copies des versions précédentes, pour ne plus supposer que les autres ne s'adaptent pas. Et
    elle tient compte de sa donne : une main forte ne se joue pas comme une main plate."""
    name = "adaptatif_v3"
    model_file = "adaptation_v3.json"
    default_arm = DEFAULT_ARM_V3

    def act(self, view, rng):
        if self._arm is None:
            self._strong = float(hand_strength(view.hand, view.n_players) >= STRONG_HAND)
        return super().act(view, rng)

    def choose(self, profiles):
        return parse_arm(self.neighbors().best_many([{**p, "main": self._strong} for p in profiles]))


class AdaptiveV4Bot(AdaptiveV3Bot, SiteReaderBot):
    """Phase 5d. La v3, qui lit en plus le marché comme le lecteur du site (cotations par fenêtre de temps,
    consensus de la table, confiance apprise par joueur). Ses réglages sont appris sur des tables jouées
    avec la règle du site, où jouent des Hard simulés et des copies de ses versions précédentes."""
    name = "adaptatif_v4"
    model_file = "adaptation_v4.json"

    def end_round(self, reveal):
        AdaptiveV3Bot.end_round(self, reveal)  # le profil de la table
        SiteReaderBot.end_round(self, reveal)  # la confiance accordée à chaque joueur


class AdaptiveV4bBot(AdaptiveV4Bot):
    """Phase 5e. La v4, avec en plus des tables d'entraînement « pleines » : des copies d'un seul bot de la
    ligue. La v4 n'avait jamais vu de table où personne ne cote (des snipers), et y choisissait mal."""
    name = "adaptatif_v4b"
    model_file = "adaptation_v4b.json"


class AdaptiveV4cBot(AdaptiveV4Bot):
    """Phase 5f. La v4b, avec en plus des tables « symétriques » : un seul autre joueur face à des copies qui
    jouent toutes le même réglage, jugé au gain moyen des copies. Les autres tables jugent un réglage au
    gain d'une seule copie, qui peut gagner en achetant à un joueur qui fait perdre l'ensemble des copies."""
    name = "adaptatif_v4c"
    model_file = "adaptation_v4c.json"



class AdaptiveV4dBot(AdaptiveV4cBot):
    """Phase 5h. La v4c, qui fait d'abord la moyenne des profils des manches passées, puis interroge ses voisins une
    seule fois. La v4c les interroge manche par manche : le profil d'une seule manche ne reconnaît pas la table de
    l'exploiteur (phase 5g). Même modèle que la v4c, sans réentraînement."""
    name = "adaptatif_v4d"

    def choose(self, profiles):
        return parse_arm(self.neighbors().best_many([{**mean_profile(profiles), "main": self._strong}]))


class QuietV4cBot(AdaptiveV4cBot):
    """Phase 5g. La v4c, qui n'envoie aucun ordre pendant les `quiet` premières secondes de chaque manche : d'après
    DiSilvio, Luo et Ozerov (arXiv 2110.00879, tableau 3), échanger tôt coûte, quand les valeurs bougent encore.
    Elle lit quand même le marché : son choix de réglage et sa lecture du site ne changent pas."""
    name = "v4c_calme_60"
    quiet = 60.0

    def act(self, view, rng):
        action = super().act(view, rng)
        return None if view.time < self.quiet else action


class QuietV4cBot30(QuietV4cBot):
    name, quiet = "v4c_calme_30", 30.0

# --- Apprentissage hors ligne -------------------------------------------------------------------

TRAIN_SEED, VALID_SEED = 9, 10
POOL = {**ZOO, "menteur": ABNORMAL["menteur"]}
# Des tables tirées dans la ligue, avec une part de tables pleines de marginaux : ce sont celles
# où les copies se font concurrence, le cas que le test de minorité punit.
CHOICES = list(POOL) + ["marginal"] * 4


def arm_bot(arm, base=MarginalBot):
    spread, edge, *late = arm
    settings = {"spread": spread, "edge": edge}
    if late:
        settings["spread_late"], settings["edge_late"] = late
    return type("Arm", (base,), settings)


# --- Phase 5b : entraînement contre ses propres copies -------------------------------------------

V3_SEED = 11
ARMS_V3 = [(6, 3, 6, 3), (8, 1, 8, 1), (10, 3, 10, 3), (12, 3, 12, 3)]
V3_PROFILES = 10  # profils gardés par table et par réglage (comme la version 2)


def version_bot(name):
    """Un joueur d'une table d'entraînement : un bot de la ligue, ou une version du bot adaptatif.
    adaptatif_v3_<k> : la version entraînée au tour k (modeles/adaptation_v3_<k>.json)."""
    if name in POOL:
        return POOL[name]
    if name == AdaptiveV2Bot.name:
        return AdaptiveV2Bot
    if name == AdaptiveV3Bot.name:
        return AdaptiveV3Bot
    if name == HardBot.name:
        return HardBot
    if name == AdaptiveV4bBot.name:
        return AdaptiveV4bBot
    version, k = re.fullmatch(r"adaptatif_(v[34])_(\d+)", name).groups()
    cls = {"v3": AdaptiveV3Bot, "v4": AdaptiveV4Bot}[version]
    return type(f"Adaptive{version.upper()}_{k}", (cls,), {"name": name, "model_file": f"adaptation_{version}_{k}.json"})


def table_opponents_v3(i, base, previous):
    """La table d'entraînement numéro i de la phase 5b : sa graine et les noms de ses adversaires.
    Une table sur deux ressemble au test de minorité : des copies d'une version précédente du bot
    adaptatif, plus un seul autre joueur. Les autres tables sont tirées dans la ligue, versions comprises."""
    seed = base * 1000 + i
    rng = random.Random(seed)
    n = rng.choice((4, 5))
    if previous and rng.random() < 0.5:
        return seed, [rng.choice(previous)] * (n - 2) + [rng.choice(list(POOL))]
    return seed, [rng.choice(CHOICES + previous * 2) for _ in range(n - 1)]


def _table_v3(job):
    """Pour une table : le gain de chaque réglage, séparé selon que ma donne est forte ou plate, et
    quelques profils d'une manche vus avec chaque réglage. Parties de `rounds` manches, rejouées à
    chaque siège sur les mêmes donnes pour tous les réglages ; la première manche, où les versions
    adaptatives ne se sont pas encore adaptées, ne compte pas dans les gains."""
    i, base, deals, rounds, previous, arms, site = job  # site (phase 5d) : règle du site, tables de la v4,
    # réglages joués par le lecteur du site ; "full" (phase 5e) : les tables pleines de la v4b ;
    # "symmetric" (phase 5f) : un seul autre joueur, toutes les autres places au réglage mesuré
    tables = {"full": table_opponents_full, "symmetric": table_opponents_symmetric}.get(
        site, table_opponents_v4 if site else table_opponents_v3)
    seed, names = tables(i, base, previous)
    opponents = [version_bot(n) for n in names if n != SELF]
    n = len(names) + 1
    gains, samples = {}, []
    for arm in map(tuple, arms):
        profits = {0.0: [], 1.0: []}
        for d in range(deals):
            deal_seed = seed * 1_000_000 + d
            for seat in range(n):
                me = arm_bot(arm, SiteReaderBot if site else MarginalBot)
                if site == "symmetric":  # seat : la place de l'autre joueur ; on compte toutes les copies
                    bots, mine = [me] * n, [s for s in range(n) if s != seat]
                    bots[seat] = opponents[0]
                else:
                    bots, mine = opponents[:seat] + [me] + opponents[seat:], [seat]
                memories = [{} for _ in bots]
                for r in range(rounds):
                    result = play_round(bots, seed=deal_seed if r == 0 else f"{deal_seed}:{r}", memories=memories,
                                        single_quote=bool(site))
                    for s in mine:
                        strong = float(hand_strength(result.log["hands"][s], n) >= STRONG_HAND)
                        if r > 0 or rounds == 1:
                            profits[strong].append(result.profits[s])
                    s = mine[0]
                    strong = float(hand_strength(result.log["hands"][s], n) >= STRONG_HAND)
                    if seat == 0 and len([x for x in samples if x[0] == arm]) < V3_PROFILES:  # donnes variées
                        samples.append((arm, table_profile(result.events, s, result.log["duration"], n), strong))
        overall = statistics.fmean(profits[0.0] + profits[1.0])
        gains[arm_key(arm)] = {str(c): statistics.fmean(v) if v else overall for c, v in profits.items()}
        gains[arm_key(arm)]["share_strong"] = len(profits[1.0]) / len(profits[0.0] + profits[1.0])
    return {"names": names, "gains": gains, "samples": [(arm_key(a), f, c) for a, f, c in samples]}


def v3_rows(tables):
    """Les lignes du modèle : (profil d'une manche + force de la main, gain de chaque réglage pour cette force)."""
    return [({**f, "main": c}, {a: g[str(c)] for a, g in t["gains"].items()})
            for t in tables for _a, f, c in t["samples"]]


def v3_cross_validation(tables, default=DEFAULT_ARM_V3):
    """Chaque table jugée par un modèle construit sur les autres, à partir de 3 manches vues au réglage
    de départ. Gain moyen par manche, en pondérant mains fortes et plates comme elles arrivent."""
    scores = {"fixe": [], "choisi": [], "meilleur": []}
    for held, t in enumerate(tables):
        model = Neighbors(v3_rows(tables[:held] + tables[held + 1:]))
        seen = [f for a, f, _c in t["samples"] if a == arm_key(default)][:3]
        share = t["gains"][arm_key(default)]["share_strong"]
        total = {name: 0.0 for name in scores}
        for c, w in ((0.0, 1 - share), (1.0, share)):
            by_arm = {a: g[str(c)] for a, g in t["gains"].items()}
            chosen = model.best_many([{**f, "main": c} for f in seen])
            total["fixe"] += w * by_arm[arm_key(default)]
            total["choisi"] += w * by_arm[chosen]
            total["meilleur"] += w * max(by_arm.values())
        for name in scores:
            scores[name].append(total[name])
    return scores


def build_v3(iteration, previous, tables, deals, rounds, arms=ARMS_V3):
    """Un tour d'entraînement : mesure les tables, écrit modeles/adaptation_v3_<tour>.json et renvoie
    les mesures (pour le rapport)."""
    if tables >= 1000:
        raise ValueError("au plus 999 tables : au-delà, les graines se chevauchent")
    with Pool() as pool:
        measured = pool.map(_table_v3, [(i, V3_SEED + iteration, deals, rounds, previous, arms, False)
                                        for i in range(tables)], chunksize=1)
    model = Neighbors(v3_rows(measured))
    path = MODELS_DIR / f"adaptation_v3_{iteration}.json"
    path.write_text(json.dumps(model.to_dict(), indent=1))
    return measured, path


# --- Phase 5d : le marché du site ---------------------------------------------------------------

V4_SEED = 21


def table_opponents_v4(i, base, previous):
    """La table d'entraînement numéro i de la phase 5d. Quatre sur dix ressemblent au test de minorité
    (copies d'une version précédente, plus un seul autre joueur), trois sur dix sont des tables de Hard
    simulés comme sur le site, les autres sont tirées dans la ligue, Hard simulés et versions comprises."""
    seed = base * 1000 + i
    rng = random.Random(seed)
    n = rng.choice((4, 5))
    draw = rng.random()
    if previous and draw < 0.4:
        return seed, [rng.choice(previous)] * (n - 2) + [rng.choice(list(POOL) + [HardBot.name])]
    if draw < 0.7:
        return seed, [HardBot.name] * (n - 1)
    return seed, [rng.choice(CHOICES + [HardBot.name] * 4 + previous * 2) for _ in range(n - 1)]


V4B_SEED = 61  # loin des graines des tours de la v4 (V4_SEED + tour), pour ne pas rejouer leurs donnes
FULL_TABLE_BOTS = sorted(POOL) + [HardBot.name]


def table_opponents_full(i, base, previous=None):
    """Phase 5e, table pleine numéro i : des copies d'un seul bot de la ligue (Hard simulé compris),
    chacun à 4 puis à 5 joueurs."""
    names = FULL_TABLE_BOTS
    return base * 1000 + i, [names[i % len(names)]] * (3 + (i // len(names)) % 2)


SELF = "copie"  # aux tables symétriques : une place jouée par le réglage mesuré
V4C_SEED = 67
SYMMETRIC_BOTS = FULL_TABLE_BOTS + [AdaptiveV3Bot.name, AdaptiveV4bBot.name]


def table_opponents_symmetric(i, base, previous=None):
    """Phase 5f, table symétrique numéro i : un seul bot de la ligue (Hard simulé, v3 et v4b compris), et
    des copies du réglage mesuré à toutes les autres places, à 4 puis à 5 joueurs."""
    names = SYMMETRIC_BOTS
    return base * 1000 + i, [names[i % len(names)]] + [SELF] * (2 + (i // len(names)) % 2)


def build_v4b(report, tables, deals, rounds, arms=ARMS_V3, kind="full"):
    """La v4b : les tables du rapport d'entraînement de la v4 (`report`, son dernier tour), plus `tables`
    tables pleines. Écrit modeles/adaptation_v4b.json. Renvoie (toutes les tables mesurées, chemin).
    kind="symmetric" (phase 5f) : la v4c, le rapport de la v4b plus des tables symétriques."""
    if tables >= 1000:
        raise ValueError("au plus 999 tables : au-delà, les graines se chevauchent")
    base = json.loads(Path(report).read_text())["tables"]
    if set(base[0]["gains"]) != {arm_key(a) for a in arms}:
        raise ValueError(f"--arms doit être celui du rapport : {', '.join(base[0]['gains'])}")
    seed, bot = {"full": (V4B_SEED, AdaptiveV4bBot), "symmetric": (V4C_SEED, AdaptiveV4cBot)}[kind]
    with Pool() as pool:
        full = pool.map(_table_v3, [(i, seed, deals, rounds, [], arms, kind) for i in range(tables)], chunksize=1)
    measured = base + full
    path = MODELS_DIR / bot.model_file
    path.write_text(json.dumps(Neighbors(v3_rows(measured)).to_dict(), indent=1))
    return measured, path


def build_v4(iteration, previous, tables, deals, rounds, arms=ARMS_V3):
    """Un tour d'entraînement de la v4 : écrit modeles/adaptation_v4_<tour>.json."""
    if tables >= 1000:
        raise ValueError("au plus 999 tables : au-delà, les graines se chevauchent")
    with Pool() as pool:
        measured = pool.map(_table_v3, [(i, V4_SEED + iteration, deals, rounds, previous, arms, True)
                                        for i in range(tables)], chunksize=1)
    path = MODELS_DIR / f"adaptation_v4_{iteration}.json"
    path.write_text(json.dumps(Neighbors(v3_rows(measured)).to_dict(), indent=1))
    return measured, path


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
    parser.add_argument("--v3", type=int, metavar="TOUR", help="phase 5b : un tour d'entraînement contre ses copies")
    parser.add_argument("--v4", type=int, metavar="TOUR", help="phase 5d : un tour d'entraînement sur le marché du site")
    parser.add_argument("--v4b", metavar="RAPPORT", help="phase 5e : la v4 du rapport, plus --tables tables pleines")
    parser.add_argument("--v4c", metavar="RAPPORT", help="phase 5f : la v4b du rapport, plus --tables tables symétriques")
    parser.add_argument("--previous", nargs="*", default=[], help="versions précédentes, placées aux tables (avec --v3)")
    parser.add_argument("--rounds", type=int, default=3, help="manches par partie (avec --v3)")
    parser.add_argument("--arms", nargs="+", help="réglages possibles, « spread,marge,spread fin,marge fin » (avec --v3)")
    args = parser.parse_args()
    if sum(x is not None for x in (args.v3, args.v4, args.v4b, args.v4c)) > 1:
        parser.error("--v3, --v4, --v4b ou --v4c, un seul à la fois")
    if args.v3 is not None or args.v4 is not None or args.v4b or args.v4c:
        from figgie.evaluate import mean_ci
        arms = [parse_arm(a) for a in args.arms] if args.arms else ARMS_V3
        if DEFAULT_ARM_V3 not in arms:
            parser.error(f"--arms doit contenir le réglage de départ {arm_key(DEFAULT_ARM_V3)}")
        for name in args.previous:
            if (name not in POOL and name not in (AdaptiveV2Bot.name, AdaptiveV3Bot.name)
                    and not re.fullmatch(r"adaptatif_v[34]_\d+", name)):
                parser.error(f"--previous : version inconnue {name} (bot de la ligue, adaptatif_v2, adaptatif_v3 "
                             "ou adaptatif_v3_<tour>, adaptatif_v4_<tour>)")
        if args.v4b:  # --previous : seulement pour retrouver les tables façon minorité du rapport
            measured, path = build_v4b(args.v4b, args.tables, args.deals, args.rounds, arms)
            print(f"v4b : {args.v4b}, plus {args.tables} tables pleines, {args.deals} donnes, parties de {args.rounds} manches")
        elif args.v4c:
            measured, path = build_v4b(args.v4c, args.tables, args.deals, args.rounds, arms, kind="symmetric")
            print(f"v4c : {args.v4c}, plus {args.tables} tables symétriques, {args.deals} donnes, parties de {args.rounds} manches")
        else:
            build = build_v4 if args.v4 is not None else build_v3
            iteration = args.v4 if args.v4 is not None else args.v3
            measured, path = build(iteration, args.previous, args.tables, args.deals, args.rounds, arms)
            print(f"{'v4, règle du site, ' if args.v4 is not None else ''}Tour {iteration}, versions aux tables : {', '.join(args.previous) or 'aucune'}, {args.tables} tables, "
                  f"{args.deals} donnes, parties de {args.rounds} manches")
        scores = v3_cross_validation(measured)
        print("Validation croisée (gain moyen $/manche, écart au réglage fixe) :")
        for name, values in scores.items():
            diff = mean_ci([v - f for v, f in zip(values, scores["fixe"])])
            print(f"  {name:9s} {statistics.fmean(values):+6.2f}   écart {diff[0]:+.2f} [{diff[1]:+.2f} ; {diff[2]:+.2f}]")
        for c, label in ((0.0, "main plate"), (1.0, "main forte")):
            picks = {}
            for i, t in enumerate(measured):
                if args.previous and t["names"].count(t["names"][0]) >= len(t["names"]) - 1 and t["names"][0] in args.previous:
                    seen = [f for a, f, _ in t["samples"] if a == arm_key(DEFAULT_ARM_V3)][:3]
                    model = Neighbors(v3_rows(measured[:i] + measured[i + 1:]))  # hors échantillon, comme la validation croisée
                    a = model.best_many([{**f, "main": c} for f in seen])
                    picks[a] = picks.get(a, 0) + 1
            if picks:
                print(f"  tables façon test de minorité, {label} : " + ", ".join(f"{a} x{n}" for a, n in sorted(picks.items())))
        print(f"Modèle écrit dans {path}")
        if args.report:
            Path(args.report).write_text(json.dumps({"args": vars(args), "tables": measured, "scores": scores}, indent=1))
        return
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
