"""Le zoo d'adversaires. Chaque bot reçoit une View (son information) et un générateur aléatoire.

Tous sauf l'aléatoire suivent la même mécanique (ValueBot) : estimer ce que vaut une carte
de chaque couleur, prendre les cotations avantageuses, sinon coter autour de cette valeur.
Ils diffèrent par l'estimation de la valeur et par leur tempérament.
"""
from math import ceil, comb, floor

from figgie.engine import GOAL_CARD_VALUE, SUITS, TWIN


class RandomBot:
    """Agit une fois sur trois, au hasard : coter à un prix tiré entre 1 et 20 $, ou prendre une cotation."""
    name = "aleatoire"

    def act(self, view, rng):
        if rng.random() > 1 / 3:
            return None
        suit = rng.choice(SUITS)
        kind = rng.choice(("bid", "ask", "buy", "sell"))
        if kind in ("bid", "ask"):
            return (kind, suit, rng.randint(1, 20))
        return (kind, suit)


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

    rate   : probabilité d'agir à chaque tick
    spread : écart entre ma valeur et mes cotations
    edge   : avantage minimal pour prendre une cotation (None = ne prend jamais)
    """
    rate, spread, edge = 0.5, 2, 0

    def __init__(self):
        self._values = None

    def values(self, hand, rng):
        raise NotImplementedError

    def act(self, view, rng):
        if self._values is None:
            # Valeurs calculées une fois, sur la donne : les cartes achetées ensuite ne changent pas le paquet.
            self._values = self.values(dict(view.hand), rng)
        if rng.random() > self.rate:
            return None
        values = self._values
        suits = list(SUITS)
        rng.shuffle(suits)
        for s in suits:
            action = self._decide(view, s, values[s])
            if action:
                return action
        return None

    def _decide(self, view, s, value):
        bid, ask = view.book[s]["bid"], view.book[s]["ask"]
        if self.edge is not None:
            if ask and ask[1] != view.seat and ask[0] <= value - self.edge and ask[0] <= view.cash:
                return ("buy", s)
            if bid and bid[1] != view.seat and bid[0] >= value + self.edge and view.hand[s] > 0:
                return ("sell", s)
        my_bid = floor(value - self.spread)
        if my_bid >= 1 and my_bid <= view.cash and (not bid or my_bid > bid[0]) and (not ask or my_bid < ask[0]):
            return ("bid", s, my_bid)
        my_ask = max(1, ceil(value + self.spread))
        if view.hand[s] > 0 and (not ask or my_ask < ask[0]) and (not bid or my_ask > bid[0]):
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
    """Même croyance que l'heuristique, mais paie cher (20 $), cote serré et agit à chaque tick."""
    name = "agressif"
    goal_value = 20
    rate, spread, edge = 1.0, 1, 0


class BayesBot(ValueBot):
    """Valeur d'une carte = P(objectif) x (10 $ + bonus fixe), probabilité tirée de ma main."""
    name = "bayesien"
    bonus = 5
    rate, spread, edge = 0.5, 2, 1

    def values(self, hand, rng):
        p = goal_posterior(hand)
        return {s: p[s] * (GOAL_CARD_VALUE + self.bonus) for s in SUITS}


class PassiveBot(BayesBot):
    """Mêmes valeurs que le bayésien, mais cote large, rarement, et ne prend jamais."""
    name = "passif"
    rate, spread, edge = 0.1, 6, None


ZOO = {bot.name: bot for bot in (RandomBot, HeuristicBot, BayesBot, AggressiveBot, PassiveBot)}
