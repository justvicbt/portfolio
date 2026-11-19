"""Le zoo d'adversaires. Chaque bot reçoit une View (son information) et un générateur aléatoire.

Tous sauf l'aléatoire suivent la même mécanique (ValueBot) : estimer ce que vaut une carte
de chaque couleur, prendre les cotations avantageuses, sinon coter autour de cette valeur.
Ils diffèrent par l'estimation de la valeur et par leur tempérament.
"""
from math import ceil, comb, floor

from figgie.engine import GOAL_CARD_VALUE, SUITS, TWIN


class RandomBot:
    """Agit au hasard, à son propre rythme : coter entre 1 et 20 $, prendre ou annuler.
    `pace` est réglé pour donner environ 67 actions par manche de 4 minutes, comme en phase 0
    (l'écart réel entre deux actions = pace + attente du prochain regard + réaction)."""
    name = "aleatoire"
    reaction, idle, pace = 0.5, 0.25, 3.3

    def __init__(self):
        self.next_time = 0.0

    def act(self, view, rng):
        if view.time < self.next_time:
            return None  # il ne réagit pas aux changements du marché, il suit son propre rythme
        self.next_time = view.time + rng.expovariate(1 / self.pace)
        suit = rng.choice(SUITS)
        kind = rng.choice(("bid", "ask", "buy", "sell", "cancel"))
        if kind == "cancel":
            return (kind, suit)
        return (kind, suit, rng.randint(1, 20))


def goal_posterior(hand):
    """P(couleur objectif = s) sachant ma main, sur les 12 compositions possibles du paquet.

    Une composition = quelle couleur a 12 cartes et laquelle en a 8. Sa vraisemblance est
    le nombre de façons de tirer ma main dans ce paquet (loi hypergéométrique).
    """
    weights = dict.fromkeys(SUITS, 0.0)
    for twelve in SUITS:
        for eight in SUITS:
            if eight == twelve:
                continue
            sizes = {s: 12 if s == twelve else 8 if s == eight else 10 for s in SUITS}
            likelihood = 1
            for s in SUITS:
                likelihood *= comb(sizes[s], hand[s])
            weights[TWIN[twelve]] += likelihood
    total = sum(weights.values())
    return {s: w / total for s, w in weights.items()}


class ValueBot:
    """Mécanique commune. Les sous-classes définissent values(), et les paramètres de tempérament.

    reaction : secondes entre ce que je vois et l'arrivée de mon action
    idle     : secondes en moyenne avant de regarder à nouveau quand rien ne bouge
    pace     : si défini, au plus une action toutes les `pace` secondes en moyenne, quelle que soit l'animation de la table
    spread   : écart entre ma valeur et mes cotations
    edge     : avantage minimal pour prendre une cotation (None = ne prend jamais)
    quotes   : False = ne cote jamais, se contente de prendre
    """
    reaction, idle, pace, spread, edge, quotes = 0.4, 1.0, None, 2, 0, True

    def __init__(self):
        self._values = None
        self.next_time = 0.0

    def values(self, hand, rng):
        raise NotImplementedError

    def act(self, view, rng):
        if self._values is None:
            # Valeurs calculées une fois, sur la donne : les cartes achetées ensuite ne changent pas le paquet.
            self._values = self.values(dict(view.hand), rng)
        if self.pace and view.time < self.next_time:
            return None
        suits = list(SUITS)
        rng.shuffle(suits)
        for s in suits:
            action = self._decide(view, s, self._values[s])
            if action:
                if self.pace:
                    self.next_time = view.time + rng.expovariate(1 / self.pace)
                return action
        return None

    def _decide(self, view, s, value):
        bid, ask = view.best(s, "bid"), view.best(s, "ask")  # meilleures cotations des autres
        if self.edge is not None:
            if ask and ask[0] <= value - self.edge and ask[0] <= view.cash:
                return ("buy", s, ask[0])  # le prix vu : refusé s'il a empiré entre-temps
            if bid and bid[0] >= value + self.edge and view.hand[s] > 0:
                return ("sell", s, bid[0])
        if not self.quotes:
            return None
        # Mes cotations restent du bon côté des autres : prendre, c'est la règle ci-dessus qui en décide.
        my_bid = floor(value - self.spread)
        if ask:
            my_bid = min(my_bid, ask[0] - 1)
        my_ask = max(1, ceil(value + self.spread))
        if bid:
            my_ask = max(my_ask, bid[0] + 1)
        if 1 <= my_bid <= view.cash and view.mine(s, "bid") != my_bid and my_bid < (view.mine(s, "ask") or 10**9):
            return ("bid", s, my_bid)
        if view.hand[s] > 0 and view.mine(s, "ask") != my_ask and my_ask > (view.mine(s, "bid") or 0):
            return ("ask", s, my_ask)
        return None


class HeuristicBot(ValueBot):
    """Suppose que ma couleur la plus longue est celle de 12 cartes : sa jumelle vaut 12 $, le reste 0 $."""
    name = "heuristique"
    goal_value = 12

    def values(self, hand, rng):
        most = max(hand.values())
        longest = rng.choice([s for s in SUITS if hand[s] == most])  # égalité tirée au sort, sans biais de couleur
        return {s: self.goal_value if s == TWIN[longest] else 0 for s in SUITS}


class AggressiveBot(HeuristicBot):
    """Même croyance que l'heuristique, mais paie cher (20 $), cote serré et réagit vite."""
    name = "agressif"
    goal_value = 20
    reaction, idle, spread, edge = 0.2, 0.3, 1, 0


class BayesBot(ValueBot):
    """Valeur d'une carte = P(objectif) x (10 $ + bonus fixe), probabilité tirée de ma main."""
    name = "bayesien"
    bonus = 5
    spread, edge = 2, 1

    def values(self, hand, rng):
        p = goal_posterior(hand)
        return {s: p[s] * (GOAL_CARD_VALUE + self.bonus) for s in SUITS}


class PassiveBot(BayesBot):
    """Mêmes valeurs que le bayésien, mais lent, cote large, rarement, et ne prend jamais."""
    name = "passif"
    reaction, idle, pace, spread, edge = 1.0, 1.0, 5.0, 6, None


class SniperBot(BayesBot):
    """Mêmes valeurs que le bayésien, mais ne cote jamais : il guette et prend tout de suite
    les cotations mal placées. C'est le plus rapide du zoo."""
    name = "sniper"
    reaction, idle, edge, quotes = 0.15, 0.5, 1, False


ZOO = {bot.name: bot for bot in (RandomBot, HeuristicBot, BayesBot, AggressiveBot, PassiveBot, SniperBot)}
