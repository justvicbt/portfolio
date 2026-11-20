"""Le zoo d'adversaires. Chaque bot reçoit une View (son information) et un générateur aléatoire.

Tous sauf l'aléatoire suivent la même mécanique (ValueBot) : estimer ce que vaut une carte
de chaque couleur, prendre les cotations avantageuses, sinon coter autour de cette valeur.
Ils diffèrent par l'estimation de la valeur et par leur tempérament.
"""
import json
from math import ceil, floor
from pathlib import Path

from figgie.engine import GOAL_CARD_VALUE, SUITS, TWIN
from figgie.signals import OpponentModel, SignalModel
from figgie.valuation import goal_probabilities, initial_hand, known_minimums, marginal_values


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
        """Une valeur par couleur, calculée une fois sur la donne."""
        raise NotImplementedError

    def refresh(self, view, rng):
        """Met à jour les valeurs. Par défaut, calculées une fois sur la donne : les cartes achetées
        ensuite ne changent pas le paquet."""
        if self._values is None:
            self._values = self.values(dict(view.hand), rng)

    def buy_value(self, s, player):
        """Ce que me rapporte une carte de `s` achetée à `player` (None = je ne sais pas encore qui)."""
        return self._values[s]

    def sell_value(self, s, player):
        """Ce que me coûte une carte de `s` vendue à `player` (None = je ne sais pas encore qui)."""
        return self._values[s]

    def act(self, view, rng):
        if self.pace and view.time < self.next_time:
            return None
        self.refresh(view, rng)
        suits = list(SUITS)
        rng.shuffle(suits)
        for s in suits:
            action = self._decide(view, s)
            if action:
                if self.pace:
                    self.next_time = view.time + rng.expovariate(1 / self.pace)
                return action
        return None

    def _decide(self, view, s):
        bid, ask = view.best(s, "bid"), view.best(s, "ask")  # meilleures cotations des autres : (prix, joueur)
        if self.edge is not None:
            if ask and ask[0] <= self.buy_value(s, ask[1]) - self.edge and ask[0] <= view.cash:
                return ("buy", s, ask[0])  # le prix vu : refusé s'il a empiré entre-temps
            if bid and bid[0] >= self.sell_value(s, bid[1]) + self.edge and view.hand[s] > 0:
                return ("sell", s, bid[0])
        if not self.quotes:
            return None
        # Mes cotations restent du bon côté des autres : prendre, c'est la règle ci-dessus qui en décide.
        my_bid = floor(self.buy_value(s, None) - self.spread)
        if ask:
            my_bid = min(my_bid, ask[0] - 1)
        my_ask = max(1, ceil(self.sell_value(s, None) + self.spread))
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
        p = goal_probabilities(hand, minimums=[], seat=None)  # ma main seule
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


class MarginalBot(ValueBot):
    """Phase 2. Valeur d'une carte calculée par Monte Carlo (figgie/valuation.py), majorité du pot
    comprise, selon le joueur d'en face : vendre au meneur coûte plus cher que vendre à un autre.
    Quand il prend une cotation, il sait qui est en face. Quand il affiche la sienne, il ne sait pas
    qui la prendra : il achète au prix de la pire provenance et vend au prix du pire acheteur.
    Les valeurs sont recalculées dès que sa main ou les échanges publics changent."""
    name = "marginal"
    samples = 300
    constraint_counting = False  # phase 3 : True = les cartes connues des autres ne sont qu'une contrainte
    spread, edge = 8, 1  # réglés sur les donnes d'entraînement (graine 2), voir figgie/tune.py et resultats/phase2/

    def __init__(self):
        super().__init__()
        self._key = None

    def refresh(self, view, rng):
        key = (tuple(view.hand.values()), len(view.trades))
        if key != self._key:
            mins = known_minimums(view.trades, view.n_players)
            drawn = initial_hand(view.hand, view.trades, view.seat) if self.constraint_counting else None
            self._values = marginal_values(view.hand, view.seat, view.card_counts, mins, rng, self.samples,
                                           drawn=drawn)
            self._key = key

    def buy_value(self, s, player):
        by_player = self._values[s][0]
        return by_player[player] if player is not None else min(by_player.values())

    def sell_value(self, s, player):
        by_player = self._values[s][1]
        return by_player[player] if player is not None else max(by_player.values())


MODEL_PATH = Path(__file__).resolve().parent.parent / "modeles" / "signaux.json"
UNIFORM = dict.fromkeys(SUITS, 0.25)


class ReaderBot(MarginalBot):
    """Phase 3. Le bot marginal, plus la lecture du marché : les cotations et les échanges des autres
    déplacent la probabilité de chaque couleur objectif (modèle appris, figgie/learn.py).
    Dans une partie de plusieurs manches, il apprend aussi à qui se fier : à la fin de chaque
    manche, il compare les signaux de chaque adversaire à l'objectif révélé (OpponentModel)."""
    name = "lecteur"
    constraint_counting = True
    resample = 0.03  # nouveau Monte Carlo si une probabilité a bougé de plus de 3 points
    _model = None

    @classmethod
    def model(cls):
        if cls._model is None:
            if not MODEL_PATH.exists():
                raise FileNotFoundError(f"{MODEL_PATH} manque : lancer d'abord python3 -m figgie.learn")
            data = json.loads(MODEL_PATH.read_text())
            cls._model = (SignalModel.from_dict(data), data["temper"])
        return cls._model

    def __init__(self):
        super().__init__()
        self.memory = {}  # remplacée par la mémoire de la partie quand il y en a une (play_match)
        self._feed = []   # le fil public de la manche, lu dans la vue
        self._n_seen = -1
        self._market = None

    def opponents(self):
        if "opponents" not in self.memory:
            self.memory["opponents"] = OpponentModel(self.model()[0])
        return self.memory["opponents"]

    def refresh(self, view, rng):
        self._feed = view.events
        if len(view.events) != self._n_seen:  # nouvel événement : on relit le marché
            model, temper = self.model()
            self._n_seen = len(view.events)
            self._new_market = model.posterior(UNIFORM, view.events, temper=temper,
                                               player_weights=self.opponents().weights(), me=view.seat)
        market = self._new_market
        key = (tuple(view.hand.values()), len(view.trades))
        moved = self._market is None or max(abs(market[s] - self._market[s]) for s in SUITS) > self.resample
        if key != self._key or moved:
            mins = known_minimums(view.trades, view.n_players)
            self._values = marginal_values(view.hand, view.seat, view.card_counts, mins, rng, self.samples,
                                           goal_weights=market, drawn=initial_hand(view.hand, view.trades, view.seat))
            self._key, self._market = key, market

    def end_round(self, reveal):
        self.opponents().observe_round(self._feed, reveal["goal"], me=reveal["seat"])


class CorrectedMarginalBot(MarginalBot):
    """Le marginal avec le seul comptage corrigé de la phase 3, sans lecture du marché.
    Hors du zoo : il sert à mesurer ce que rapporte chaque amélioration du lecteur séparément."""
    name = "marginal_corrige"
    constraint_counting = True


ZOO = {bot.name: bot for bot in (RandomBot, HeuristicBot, BayesBot, AggressiveBot, PassiveBot, SniperBot,
                                 MarginalBot, ReaderBot)}
