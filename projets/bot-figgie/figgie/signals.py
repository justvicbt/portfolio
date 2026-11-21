"""Lire le marché : ce que les cotations et les échanges des autres disent de la couleur objectif.

Un événement, c'est ce qu'un joueur voit à l'écran : quelqu'un affiche une offre d'achat ou
de vente, ou une carte change de main. Le marché tient le fil public de ces événements
(Market.events), que chaque bot lit dans sa vue : (instant, joueur, nature, couleur, prix),
avec nature = "bid", "ask", "bought" ou "sold".
"""
import math
from functools import lru_cache

from figgie.engine import TWIN, IllegalAction, Market


def events_from_log(log):
    """Le fil public d'une manche, reconstruit en rejouant son journal."""
    market = Market(log["hands"])
    for t, seat, action, ok, _seen_at in log["actions"]:
        if not ok:
            continue  # une action refusée n'apparaît jamais à l'écran
        try:
            market.apply(seat, action, t)
        except IllegalAction as err:
            raise ValueError(f"journal incohérent à t={t}") from err
    return market.events


PRICE_BUCKETS = ((1, 2), (3, 5), (6, 9), (10, 14), (15, 10**9))
SMOOTHING = 0.5  # pseudo-compte ajouté à chaque case : évite les rapports infinis pour un événement jamais vu


@lru_cache(maxsize=None)
def price_bucket(price):
    return next(f"{lo}-{hi}" if hi < 10**9 else f"{lo}+" for lo, hi in PRICE_BUCKETS if lo <= price <= hi)


ALL_KINDS = ("bid", "ask", "bought", "sold")


def distinct(events):
    """Chaque signal une seule fois par joueur : même nature, même couleur, même tranche de prix.
    Un joueur qui reposte dix fois la même offre n'en sait pas dix fois plus ; les compter toutes
    rendait le modèle beaucoup trop sûr de lui (mesuré sur les manches de validation)."""
    seen, out = set(), []
    for e in events:
        key = (e[1], e[2], e[3], price_bucket(e[4]))
        if key not in seen:
            seen.add(key)
            out.append(e)
    return out


def relation(suit, goal):
    """Place d'une couleur par rapport à l'objectif : l'objectif lui-même, sa jumelle (la couleur de 12), ou une autre."""
    return "goal" if suit == goal else "twin" if suit == TWIN[goal] else "other"


class SignalModel:
    """Ce que chaque type d'événement dit de la couleur objectif, appris en comptant sur des manches jouées.

    Pour un type d'événement (nature + tranche de prix), on compte combien de fois il apparaît, par
    manche, dans la couleur objectif, dans sa jumelle et dans une autre couleur. Le rapport de ces
    fréquences dit si l'événement trahit l'objectif : une offre d'achat chère est bien plus fréquente
    dans l'objectif qu'ailleurs. Ces rapports se multiplient ensuite (naïvement, comme s'ils étaient
    indépendants), d'où le paramètre `temper` qui les atténue.
    """

    def __init__(self, counts, n_rounds, reference=None, kinds=ALL_KINDS):
        self.kinds = tuple(kinds)  # natures d'événements lues ; les autres sont ignorées
        self.counts = counts  # (relation, nature, tranche) -> nombre d'événements
        self.n_rounds = n_rounds
        self.exposure = {"goal": n_rounds, "twin": n_rounds, "other": 2 * n_rounds}
        self.reference = reference  # apport moyen d'un événement sur les manches d'apprentissage (voir contrast)
        self._ratios = {}  # cache : (nature, tranche) -> rapports

    def keep(self, events):
        """Les événements que ce modèle lit : natures retenues, chaque signal une seule fois."""
        return distinct([e for e in events if e[2] in self.kinds])

    @classmethod
    def fit(cls, rounds, kinds=ALL_KINDS):
        """`rounds` : suite de (événements, couleur objectif). `kinds` : natures d'événements à apprendre."""
        rounds = [(distinct([e for e in events if e[2] in kinds]), goal) for events, goal in rounds]
        counts = {}
        for events, goal in rounds:
            for _t, _p, kind, suit, price in events:
                key = (relation(suit, goal), kind, price_bucket(price))
                counts[key] = counts.get(key, 0) + 1
        model = cls(counts, len(rounds), kinds=kinds)
        contrasts = [model.contrast(e, goal) for events, goal in rounds for e in events]
        model.reference = sum(contrasts) / len(contrasts) if contrasts else 0.0
        return model

    def _rate(self, rel, kind, bucket):
        return (self.counts.get((rel, kind, bucket), 0) + SMOOTHING) / self.exposure[rel]

    def log_ratios(self, kind, price):
        """(log du rapport objectif / autre, log du rapport jumelle / autre) pour cet événement."""
        b = price_bucket(price)
        if (kind, b) not in self._ratios:
            other = self._rate("other", kind, b)
            self._ratios[kind, b] = (math.log(self._rate("goal", kind, b) / other),
                                     math.log(self._rate("twin", kind, b) / other))
        return self._ratios[kind, b]

    def evidence(self, event, goal):
        """Ce que l'événement apporte en faveur de la vraie couleur objectif (log du rapport)."""
        _t, _p, kind, suit, price = event
        lr_goal, lr_twin = self.log_ratios(kind, price)
        return {"goal": lr_goal, "twin": lr_twin, "other": 0.0}[relation(suit, goal)]

    def contrast(self, event, goal):
        """De combien l'événement favorise la vraie couleur objectif plus que la moyenne des quatre.
        Nul en moyenne pour un joueur qui cote au hasard, positif pour un joueur qui sait quelque chose."""
        _t, _p, kind, _suit, price = event
        lr_goal, lr_twin = self.log_ratios(kind, price)
        return self.evidence(event, goal) - (lr_goal + lr_twin) / 4  # sur les 4 hypothèses, une est objectif, une jumelle

    def posterior(self, prior, events, temper=1.0, player_weights=None, me=None):
        """P(couleur objectif) après les événements. `me` : mes propres événements sont ignorés.
        `player_weights` : confiance accordée à chaque joueur (1 par défaut, 0 = ignoré)."""
        scores = {g: math.log(p) if p > 0 else -math.inf for g, p in prior.items()}
        for event in self.keep(events):
            player = event[1]
            w = temper * (player_weights or {}).get(player, 1.0)
            if player == me or w == 0:
                continue
            for g in scores:
                scores[g] += w * self.evidence(event, g)
        top = max(scores.values())
        exp = {g: math.exp(s - top) for g, s in scores.items()}
        total = sum(exp.values())
        return {g: v / total for g, v in exp.items()}

    def to_dict(self):
        return {"n_rounds": self.n_rounds, "reference": self.reference, "kinds": list(self.kinds),
                "counts": [[*k, c] for k, c in sorted(self.counts.items())]}

    @classmethod
    def from_dict(cls, data):
        return cls({(rel, kind, b): c for rel, kind, b, c in data["counts"]}, data["n_rounds"], data["reference"],
                   data.get("kinds", ALL_KINDS))


class OpponentModel:
    """La confiance que j'accorde à chaque adversaire, apprise manche après manche.

    À la fin d'une manche, l'objectif est révélé. Pour chaque adversaire, on mesure si ses
    événements pointaient vers la bonne couleur (contrast), et on compare à un joueur moyen
    de l'apprentissage. Poids 1 : aussi fiable que la moyenne. Poids 0 : ses signaux ne disent
    rien. Au début, on suppose chacun moyen ; `prior_events` règle la vitesse à laquelle les
    observations l'emportent sur cette supposition, et `cap` limite la confiance maximale.
    """

    def __init__(self, model, prior_events=10, cap=1.5):
        self.model, self.prior_events, self.cap = model, prior_events, cap
        self.total = {}  # joueur -> somme des contrasts observés
        self.count = {}  # joueur -> nombre d'événements observés

    def observe_round(self, events, goal, me):
        for event in self.model.keep(events):
            player = event[1]
            if player == me:
                continue
            self.total[player] = self.total.get(player, 0.0) + self.model.contrast(event, goal)
            self.count[player] = self.count.get(player, 0) + 1

    def weight(self, player):
        n = self.count.get(player, 0)
        if n == 0 or not self.model.reference or self.model.reference < 0:
            return 1.0  # sans référence positive, impossible de dire qui est fiable : confiance par défaut
        ratio = min(self.cap, max(0.0, self.total[player] / n / self.model.reference))
        return (self.prior_events + n * ratio) / (self.prior_events + n)

    def weights(self):
        return {p: self.weight(p) for p in self.count}


# --- Phase 5d : lire le marché du site ------------------------------------------------------------

def window(t, duration, windows):
    """Le moment de la manche où tombe l'instant t : 0 pour la première fenêtre, windows - 1 pour la dernière."""
    return min(windows - 1, int(t / duration * windows))


def top_bids(events, players):
    """Le plus haut prix d'achat proposé par chaque joueur de `players` dans chaque couleur : {(joueur, couleur): prix}."""
    top = {}
    for _t, player, kind, suit, price in events:
        if kind == "bid" and player in players and price > top.get((player, suit), 0):
            top[player, suit] = price
    return top


def consensus_events(top, players, now, duration, windows):
    """Le consensus de la table à l'instant `now` : pour chaque couleur, le plus bas des plus hauts prix
    d'achat proposés par les joueurs. Un seul joueur qui propose cher ne suffit pas à le monter.
    Rendu comme un événement par couleur, pour que le modèle l'apprenne comme les autres."""
    w = window(now, duration, windows)
    return [(now, ("consensus", w), f"cons@{w}", suit, max(1, min(top.get((p, suit), 0) for p in players)))
            for suit in "SCHD"]


class TimedSignalModel(SignalModel):
    """Phase 5d. Le modèle de signaux, avec deux différences, pour le marché du site.

    Un même événement ne dit pas la même chose au début et à la fin de la manche : sur les vraies
    manches, les cotations de la première minute ne disent presque rien de l'objectif. On apprend donc
    les rapports séparément pour chaque fenêtre de temps (nature « bid@0 » pour une offre d'achat de la
    première fenêtre). Et on ajoute le consensus de la table (consensus_events).

    Chaque événement est attribué à (joueur, fenêtre) : la confiance apprise d'une manche à l'autre
    (OpponentModel) se règle ainsi séparément pour chaque joueur et chaque moment de la manche."""

    def __init__(self, counts, n_rounds, reference=None, kinds=("bid", "ask"), windows=4, consensus=True):
        self.base_kinds, self.windows, self.consensus = tuple(kinds), windows, consensus
        timed = tuple(f"{k}@{w}" for k in kinds for w in range(windows))
        super().__init__(counts, n_rounds, reference, timed + (tuple(f"cons@{w}" for w in range(windows)) if consensus else ()))

    def features(self, events, duration, me=None):
        """Les événements des autres, marqués de leur fenêtre de temps (sans le consensus)."""
        return [(t, (p, window(t, duration, self.windows)), f"{kind}@{window(t, duration, self.windows)}", s, price)
                for t, p, kind, s, price in events if kind in self.base_kinds and p != me]

    def round_features(self, events, duration, players, me=None):
        """Toute une manche : les événements des autres, plus le consensus de `players` à la fin de chaque fenêtre."""
        out = self.features(events, duration, me)
        if self.consensus:
            for w in range(self.windows):
                end = (w + 1) * duration / self.windows - 1e-6
                out += consensus_events(top_bids([e for e in events if e[0] <= end], players), players, end,
                                        duration, self.windows)
        return out

    @classmethod
    def fit_rounds(cls, rounds, kinds=("bid", "ask"), windows=4, consensus=True):
        """`rounds` : suite de (événements, objectif, durée, nombre de joueurs) de manches simulées.
        Les événements de tous les joueurs servent à apprendre. Le consensus, lui, est pris sur tous les
        joueurs sauf le siège 0, comme en partie, où le lecteur le calcule sur les autres joueurs."""
        shape = cls({}, 0, kinds=kinds, windows=windows, consensus=consensus)
        fitted = SignalModel.fit([(shape.round_features(ev, d, range(1, n)), goal) for ev, goal, d, n in rounds],
                                 kinds=shape.kinds)
        return cls(fitted.counts, fitted.n_rounds, fitted.reference, kinds, windows, consensus)

    def to_dict(self):
        return {**super().to_dict(), "kinds": list(self.base_kinds), "windows": self.windows, "consensus": self.consensus}

    @classmethod
    def from_dict(cls, data):
        return cls({(rel, kind, b): c for rel, kind, b, c in data["counts"]}, data["n_rounds"], data["reference"],
                   data["kinds"], data["windows"], data["consensus"])


class MarketReading:
    """La lecture du marché d'une manche, tenue à jour événement par événement (le fil du site en compte
    des centaines : tout relire à chaque nouvel événement coûterait trop cher). Les poids des joueurs
    sont fixés pour la manche : ils ne changent qu'entre deux manches."""

    def __init__(self, model, temper, duration, me, players, weights=None):
        self.model, self.temper, self.duration, self.me = model, temper, duration, me
        self.players, self.weights = [p for p in players if p != me], weights or {}
        self.scores = dict.fromkeys("SCHD", 0.0)
        self._seen, self._n, self._top = set(), 0, {}

    def _add(self, event):
        player = event[1]
        key = (player, event[2], event[3], price_bucket(event[4]))
        w = self.temper * self.weights.get(player, 1.0)
        if key in self._seen or w == 0:
            return
        self._seen.add(key)
        for g in self.scores:
            self.scores[g] += w * self.model.evidence(event, g)

    def update(self, events):
        """Lit les nouveaux événements du fil (celui-ci ne fait que s'allonger pendant la manche)."""
        new = events[self._n:]
        self._n = len(events)
        for e in new:
            if e[2] == "bid" and e[1] in self.players and e[4] > self._top.get((e[1], e[3]), 0):
                self._top[e[1], e[3]] = e[4]
        for e in self.model.features(new, self.duration, self.me):
            if e[2] in self.model.kinds:
                self._add(e)

    def posterior(self, prior, now):
        scores = dict(self.scores)
        if self.model.consensus and self.players:
            for e in consensus_events(self._top, self.players, now, self.duration, self.model.windows):
                w = self.temper * self.weights.get(e[1], 1.0)
                for g in scores:
                    scores[g] += w * self.model.evidence(e, g)
        logs = {g: (math.log(p) if p > 0 else -math.inf) + scores[g] for g, p in prior.items()}
        top = max(logs.values())
        exp = {g: math.exp(s - top) for g, s in logs.items()}
        total = sum(exp.values())
        return {g: v / total for g, v in exp.items()}
