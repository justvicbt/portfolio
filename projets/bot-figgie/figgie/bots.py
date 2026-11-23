"""Le zoo d'adversaires. Chaque bot reçoit une View (son information) et un générateur aléatoire.

Tous sauf l'aléatoire suivent la même mécanique (ValueBot) : estimer ce que vaut une carte
de chaque couleur, prendre les cotations avantageuses, sinon coter autour de cette valeur.
Ils diffèrent par l'estimation de la valeur et par leur tempérament.
"""
import json
import math
from math import ceil, floor
from pathlib import Path

from figgie.engine import GOAL_CARD_VALUE, POT, SUITS, TWIN
from figgie.signals import MarketReading, OpponentModel, SignalModel, TimedSignalModel, window
from figgie.valuation import (CONFIGS, _consistent, goal_probabilities, initial_hand, known_minimums,
                              known_minimums_from_events, marginal_values)


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
    spread_late, edge_late : phase 5b, si définis, valeurs en fin de manche ; on passe en ligne droite
               de `spread` (et `edge`) au début à ces valeurs à la fin (patient au début, pressé à la fin)
    """
    reaction, idle, pace, spread, edge, quotes = 0.4, 1.0, None, 2, 0, True
    spread_late = edge_late = None

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

    def _over_time(self, view, start, late):
        if late is None:
            return start
        return start + (late - start) * min(1.0, view.time / view.duration)

    def _decide(self, view, s):
        bid, ask = view.best(s, "bid"), view.best(s, "ask")  # meilleures cotations des autres : (prix, joueur)
        edge = None if self.edge is None else self._over_time(view, self.edge, self.edge_late)
        if edge is not None:
            if ask and ask[0] <= self.buy_value(s, ask[1]) - edge and ask[0] <= view.cash:
                return ("buy", s, ask[0])  # le prix vu : refusé s'il a empiré entre-temps
            if bid and bid[0] >= self.sell_value(s, bid[1]) + edge and view.hand[s] > 0:
                return ("sell", s, bid[0])
        if not self.quotes:
            return None
        # Mes cotations restent du bon côté des autres : prendre, c'est la règle ci-dessus qui en décide.
        spread = self._over_time(view, self.spread, self.spread_late)
        my_bid = floor(self.buy_value(s, None) - spread)
        if ask:
            my_bid = min(my_bid, ask[0] - 1)
        my_ask = max(1, ceil(self.sell_value(s, None) + spread))
        if bid:
            my_ask = max(my_ask, bid[0] + 1)
        can_bid = can_ask = True
        if view.single_quote:  # phase 5c, règle du site : une offre doit battre celle qui est affichée
            mine_bid, mine_ask = view.mine(s, "bid"), view.mine(s, "ask")
            if (mine_bid is not None and my_bid < mine_bid) or (mine_ask is not None and my_ask > mine_ask):
                return ("cancel", s)  # je ne peux pas reculer mon prix : je retire la cotation
            can_bid = not bid or my_bid > bid[0]
            can_ask = not ask or my_ask < ask[0]
        if can_bid and 1 <= my_bid <= view.cash and view.mine(s, "bid") != my_bid and my_bid < (view.mine(s, "ask") or 10**9):
            return ("bid", s, my_bid)
        if can_ask and view.hand[s] > 0 and view.mine(s, "ask") != my_ask and my_ask > (view.mine(s, "bid") or 0):
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

    ask_counting = False  # phase 5b : True = une vente proposée prouve aussi qu'on a la carte

    def __init__(self):
        super().__init__()
        self._key = None
        self._mins, self._seen = None, 0

    def minimums(self, view):
        if not self.ask_counting:
            return known_minimums(view.trades, view.n_players)
        self._mins = known_minimums_from_events(view.events[self._seen:], view.n_players, self._mins)
        self._seen = len(view.events)
        return self._mins

    def refresh(self, view, rng):
        mins = self.minimums(view)
        key = (tuple(view.hand.values()), len(view.trades), str(mins) if self.ask_counting else None)
        if key != self._key:
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


MODELS_DIR = Path(__file__).resolve().parent.parent / "modeles"
MODEL_PATH = MODELS_DIR / "signaux.json"
_LOADED = {}  # fichier de modèle -> objet chargé, une fois par processus


def load_model(filename, build, command):
    """Charge un modèle appris (modeles/<filename>) une seule fois. `build` transforme le JSON en objet."""
    if filename not in _LOADED:
        path = MODELS_DIR / filename
        if not path.exists():
            raise FileNotFoundError(f"{path} manque : lancer d'abord python3 -m {command}")
        _LOADED[filename] = build(json.loads(path.read_text()))
    return _LOADED[filename]
UNIFORM = dict.fromkeys(SUITS, 0.25)


class ReaderBot(MarginalBot):
    """Phase 3. Le bot marginal, plus la lecture du marché : les cotations et les échanges des autres
    déplacent la probabilité de chaque couleur objectif (modèle appris, figgie/learn.py).
    Dans une partie de plusieurs manches, il apprend aussi à qui se fier : à la fin de chaque
    manche, il compare les signaux de chaque adversaire à l'objectif révélé (OpponentModel)."""
    name = "lecteur"
    constraint_counting = True
    resample = 0.03  # nouveau Monte Carlo si une probabilité a bougé de plus de 3 points
    model_file = "signaux.json"

    @classmethod
    def model(cls):
        return load_model(cls.model_file, lambda data: (SignalModel.from_dict(data), data["temper"]), "figgie.learn")

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
        if self.market_key(view) != self._n_seen:  # nouvel événement : on relit le marché
            self._n_seen = self.market_key(view)
            self._new_market = self.market(view)
        market = self._new_market
        key = (tuple(view.hand.values()), len(view.trades))
        moved = self._market is None or max(abs(market[s] - self._market[s]) for s in SUITS) > self.resample
        if key != self._key or moved:
            mins = self.minimums(view)
            self._values = marginal_values(view.hand, view.seat, view.card_counts, mins, rng, self.samples,
                                           goal_weights=market, drawn=initial_hand(view.hand, view.trades, view.seat))
            self._key, self._market = key, market

    def market_key(self, view):
        """Ce qui doit changer pour que la lecture du marché change : ici, le nombre d'événements du fil."""
        return len(view.events)

    def market(self, view):
        """P(couleur objectif) d'après le marché seul."""
        model, temper = self.model()
        return model.posterior(UNIFORM, view.events, temper=temper, player_weights=self.opponents().weights(),
                               me=view.seat)

    def end_round(self, reveal):
        self.opponents().observe_round(self._feed, reveal["goal"], me=reveal["seat"])


class SiteReaderBot(ReaderBot):
    """Phase 5d. Le lecteur, avec le modèle de signaux appris sur le marché du site (figgie.learn --site) :
    les cotations lues par fenêtre de temps, plus le consensus de la table. La confiance apprise d'une
    manche à l'autre se règle par joueur et par fenêtre de temps."""
    name = "lecteur_site"
    signals_file = "signaux_site.json"  # pas model_file : la v4 hérite aussi du bot adaptatif, qui a le sien

    @classmethod
    def model(cls):
        return load_model(cls.signals_file, lambda data: (TimedSignalModel.from_dict(data), data["temper"]),
                          "figgie.learn --site")

    def __init__(self):
        super().__init__()
        self._reading = None

    def market_key(self, view):
        # le consensus dépend aussi de la fenêtre de temps, qui peut changer sans nouvel événement
        return len(view.events), window(view.time, view.duration, self.model()[0].windows)

    def market(self, view):
        if self._reading is None:  # premier regard de la manche
            model, temper = self.model()
            self._reading = MarketReading(model, temper, view.duration, view.seat, range(view.n_players),
                                          self.opponents().weights())
        self._reading.update(view.events)
        return self._reading.posterior(UNIFORM, view.time)

    def end_round(self, reveal):
        if self._reading is None:
            return  # aucun regard sur le marché pendant la manche
        features = self.model()[0].round_features(self._feed, self._reading.duration, self._reading.players,
                                                  me=reveal["seat"])
        self.opponents().observe_round(features, reveal["goal"], me=None)


class ExploiterBot(BayesBot):
    """Phase 4, trouvé par figgie.exploit : le meilleur adversaire du marginal (et du lecteur à 4 joueurs)
    quand il joue seul face à leurs copies. Il cote plus près de sa valeur qu'eux, donc ses prix sont
    les meilleurs du carnet, mais il est plus exigeant pour prendre."""
    name = "exploiteur"
    reaction, idle, spread, edge = 0.3, 1.0, 6, 3


class ReaderExploiterBot(MarginalBot):
    """Phase 4, trouvé par figgie.exploit : le meilleur adversaire du lecteur à 5 joueurs."""
    name = "exploiteur_lecteur"
    reaction, idle, pace, spread, edge = 0.2, 0.8, 2.0, 4, 3


class ImitatorBot:
    """Phase 5g : le « bottom feeder » de DiSilvio, Luo et Ozerov (arXiv 2110.00879), réécrit d'après l'article.
    Il ne calcule aucune valeur : pour une couleur, il prend la moyenne des derniers prix d'achat et des derniers
    prix de vente de ses proies (tous les autres joueurs), puis achète à un prix tiré entre 1 $ et cette valeur,
    ou vend entre cette valeur et le double. Un prix qui atteint la meilleure cotation d'en face la prend.
    L'article exige 4 prix de chaque côté ; je prends les 4 derniers dès qu'il y en a un de chaque côté,
    sinon il n'agit presque jamais sur nos tables. Il regarde toutes les 2 s en moyenne, au hasard une couleur et un côté."""
    name = "imitateur"
    pace, depth = 2.0, 4

    def __init__(self):
        self.next_time = 0.0

    def value(self, view, suit, side):
        prey = {}
        for _t, player, kind, s, price in view.events:
            if s == suit and player != view.seat and kind != "cancel":
                buys, sells = prey.setdefault(player, ([], []))
                (buys if kind in ("bid", "bought") else sells).append(price)
        means = [(sum(b[-self.depth:]) / len(b[-self.depth:]) + sum(a[-self.depth:]) / len(a[-self.depth:])) / 2
                 for b, a in prey.values() if b and a]
        return max(1, round(sum(means) / len(means))) if means else None

    def act(self, view, rng):
        if view.time < self.next_time:
            return None
        self.next_time = view.time + rng.expovariate(1 / self.pace)
        side, suit = rng.choice(("bid", "ask")), rng.choice(SUITS)
        if side == "ask" and not view.hand[suit]:
            return None
        value = self.value(view, suit, side)
        if value is None:
            return None
        price = rng.randint(1, value) if side == "bid" else rng.randint(value, 2 * value)
        other, mine = view.best(suit, "ask" if side == "bid" else "bid"), view.mine(suit, "ask" if side == "bid" else "bid")
        if other and (price >= other[0] if side == "bid" else price <= other[0]):
            return ("buy" if side == "bid" else "sell", suit, other[0])
        if mine is not None and (price >= mine if side == "bid" else price <= mine):
            return None  # croiserait ma propre cotation : le moteur refuse
        return (side, suit, price)


class FundamentalistBot(ImitatorBot):
    """Phase 5g : le « fundamentalist » de DiSilvio, Luo et Ozerov (arXiv 2110.00879, section 2.3), réécrit
    d'après l'article. Même façon de coter que l'imitateur, mais sa valeur vient des cartes : chacun des 12 paquets
    pèse le nombre de façons d'y trouver ma main et les cartes vues dans les échanges, et un paquet dont la couleur
    est l'objectif donne 10 $ plus une part géométrique de la majorité, p (1 - r) r^h / (1 - r^x), où h est mon
    nombre de cartes, x la majorité sûre (5 ou 6) et p le reste du pot. Vendre vaut la même chose avec h - 1.
    L'article ne fixe pas r (r > 1) : 1,7 comme FiggieServer, et la variante 3,5 comme le dépôt de Cornell.
    shortcut: pas de retrait des cotations dépassées (la « lazy deletion » de l'article) ; avec la règle du site,
    sa valeur ne bouge qu'après un échange, qui vide déjà le carnet."""
    name = "fondamentaliste"
    r = 1.7

    def value(self, view, suit, side):
        _mins, _known, weights = _consistent(view.hand, view.seat, known_minimums(view.trades, view.n_players), None, None)
        h = view.hand[suit] - (side == "ask")
        total, value = 0.0, 0.0
        for (twelve, _eight, sizes), w in zip(CONFIGS, weights):
            total += w
            if TWIN[twelve] == suit:
                x, p = (5 if sizes[suit] == 8 else 6), POT - GOAL_CARD_VALUE * sizes[suit]
                value += w * (GOAL_CARD_VALUE + (p * (1 - self.r) * self.r ** h / (1 - self.r ** x) if h < x else 0))
        return max(1, round(value / total))


class FundamentalistBot35(FundamentalistBot):
    name, r = "fondamentaliste_35", 3.5


class FiggieAutoBot:
    """Phase 5g : base de trois stratégies décrites dans 0xDub/figgie-auto (pas de licence : réécrites d'après leur
    description, sans reprendre le code). Il regarde le marché toutes les 2 à 4 s et fait une des actions qu'il
    voudrait faire, tirée au hasard (figgie-auto les envoie toutes d'un coup). Comme là-bas, un carnet vide se lit
    comme une offre d'achat à 0 $ et une offre de vente à 99 $, et il ne cote que pour battre l'offre affichée."""

    def __init__(self):
        self.next_time = 0.0

    def act(self, view, rng):
        if view.time < self.next_time:
            return None
        self.next_time = view.time + rng.uniform(2.0, 4.0)
        wishes = [a for a in self.wishes(view, view.duration - view.time) if a]
        return rng.choice(wishes) if wishes else None

    @staticmethod
    def shown(view, suit, side):
        """(prix affiché, est-ce le mien ?)"""
        other, mine = view.best(suit, side), view.mine(suit, side)
        prices = [(q, False) for q in [other and other[0]] if q] + ([(mine, True)] if mine is not None else [])
        if not prices:
            return (0 if side == "bid" else 99), False
        return (max if side == "bid" else min)(prices, key=lambda q: q[0])

    def quote(self, view, suit, side, price):
        """Ma cotation si elle bat l'offre affichée ; prend l'offre d'en face si elle la croise."""
        shown, mine = self.shown(view, suit, side)
        if mine or price < 1 or (price <= shown if side == "bid" else price >= shown):
            return None
        if side == "ask" and not view.hand[suit]:
            return None
        other = view.best(suit, "ask" if side == "bid" else "bid")
        if other and (price >= other[0] if side == "bid" else price <= other[0]):
            return ("buy" if side == "bid" else "sell", suit, other[0])
        return (side, suit, price)


class SellerBot(FiggieAutoBot):
    """« Seller » : il ne fait que vendre, à un prix plancher qui baisse avec le temps, et prend les offres d'achat
    assez hautes. (prix pris, prix proposé) : (6, 8) la première minute, (5, 6), (4, 6), puis (3, 4) la dernière."""
    name = "vendeur"

    def wishes(self, view, left):
        take, limit = (6, 8) if left >= 180 else (5, 6) if left > 120 else (4, 6) if left > 60 else (3, 4)
        for suit in SUITS:
            if view.hand[suit]:
                bid = view.best(suit, "bid")
                if bid and bid[0] >= take:
                    yield ("sell", suit, bid[0])
                yield self.quote(view, suit, "ask", limit)


class MantisBot(FiggieAutoBot):
    """« PrayingMantis » : pendant 3 minutes, il vend chaque couleur 1 $ sous l'offre de vente affichée si elle vaut
    7 $ ou plus ; la dernière minute, il achète à 9 $ au plus la couleur dont le dernier échange a été le plus cher.
    Comme dans figgie-auto : sans aucun échange, toutes les couleurs valent 0 et c'est le pique qui est choisi, et à
    60 s exactement de la fin, les deux fenêtres se touchent."""
    name = "mante"

    def wishes(self, view, left):
        if left >= 60:
            for suit in SUITS:
                ask, _mine = self.shown(view, suit, "ask")
                if view.hand[suit] and ask >= 7:
                    yield self.quote(view, suit, "ask", ask - 1)
        if left <= 60:
            last = {}
            for _buyer, _seller, suit, price in view.trades:
                last[suit] = price
            dearest = max(SUITS, key=lambda s: last.get(s, 0))  # à égalité, la première couleur
            ask = view.best(dearest, "ask")
            if ask and ask[0] <= 9:
                yield ("buy", dearest, ask[0])


class TiltBot(FiggieAutoBot):
    """« TiltInventory » : il parie sur la couleur dont il avait le plus de cartes au départ. Il l'achète (il prend une
    offre de vente à 5 $ au plus, sinon il propose 1 $ de plus que l'offre d'achat affichée, jusqu'à 8 $), et vend
    les autres 1 $ sous l'offre de vente affichée tant qu'elle dépasse 4 $, puis à 3 $ les 30 dernières secondes."""
    name = "parieur"

    def wishes(self, view, left):
        start = initial_hand(view.hand, view.trades, view.seat)
        bet = max(SUITS, key=lambda s: start[s])  # à égalité, la première couleur
        for suit in SUITS:
            if suit != bet and view.hand[suit]:
                ask, _mine = self.shown(view, suit, "ask")
                if left > 30:
                    if ask > 4:
                        yield self.quote(view, suit, "ask", ask - 1)
                else:
                    yield self.quote(view, suit, "ask", 3)
        ask = view.best(bet, "ask")
        if ask and ask[0] <= 5:
            yield ("buy", bet, ask[0])
        bid, _mine = self.shown(view, bet, "bid")
        if bid < 8:
            yield self.quote(view, bet, "bid", bid + 1)


class CorrectedMarginalBot(MarginalBot):
    """Le marginal avec le seul comptage corrigé de la phase 3, sans lecture du marché.
    Hors du zoo : il sert à mesurer ce que rapporte chaque amélioration du lecteur séparément."""
    name = "marginal_corrige"
    constraint_counting = True


class CountingBot(CorrectedMarginalBot):
    """Phase 5b, étape 1 : le marginal corrigé, qui compte aussi les ventes proposées par les autres."""
    name = "compteur"
    ask_counting = True


class IdleBot:
    """Phase 4, comportement anormal : un joueur qui ne fait jamais rien (déconnecté, ou qui attend)."""
    name = "inactif"
    idle = 30.0

    def act(self, view, rng):
        return None


class SpamBot:
    """Phase 4, comportement anormal : envoie des cotations au hasard aussi vite que le moteur le permet."""
    name = "spammeur"
    reaction, idle = 0.001, 0.01

    def act(self, view, rng):
        suit = rng.choice(SUITS)
        kind = rng.choice(("bid", "ask", "cancel"))
        return (kind, suit) if kind == "cancel" else (kind, suit, rng.randint(1, 20))


class LiarBot(MarginalBot):
    """Phase 4, comportement anormal : il joue comme le marginal, mais affiche de temps en temps une
    offre d'achat chère (`fake_price`) dans la couleur qu'il juge la moins utile, puis l'annule.
    Il vise les bots qui lisent le marché. Si quelqu'un lui vend pendant ce temps, il paie cher."""
    name = "menteur"
    fake_price, fake_for, fake_every = 12, 1.5, 6.0  # prix, durée de l'offre (s), écart entre deux mensonges (s)

    def __init__(self):
        super().__init__()
        self.fake, self.fake_until, self.next_fake = None, 0.0, 0.0

    def act(self, view, rng):
        self.refresh(view, rng)
        if self.fake and view.mine(self.fake, "bid") != self.fake_price:
            self.fake = None  # effacée par un échange, ou prise : le mensonge est terminé
        if self.fake and view.time >= self.fake_until:
            suit, self.fake = self.fake, None
            return ("cancel", suit)
        if not self.fake and view.time >= self.next_fake and view.cash >= self.fake_price:
            # Une couleur où l'offre ne croise aucune vente, ni celle des autres ni la mienne : sinon elle
            # serait exécutée ou refusée. Son retrait annule aussi ma vraie vente dans cette couleur ;
            # je la reposte au regard suivant, une fois le mensonge terminé.
            safe = [s for s in SUITS if (view.mine(s, "ask") or 10**9) > self.fake_price
                    and (not view.best(s, "ask") or view.best(s, "ask")[0] > self.fake_price)]
            if safe:
                self.fake = min(safe, key=lambda s: self.buy_value(s, None))
                self.fake_until, self.next_fake = view.time + self.fake_for, view.time + self.fake_every
                return ("bid", self.fake, self.fake_price)
        return super().act(view, rng)

    def _decide(self, view, s):
        return None if s == self.fake else super()._decide(view, s)


ABNORMAL = {bot.name: bot for bot in (IdleBot, SpamBot, LiarBot)}


class HardBot:
    """Phase 5c : une imitation des bots « Hard » de figgie.com, réglée sur les journaux de Rasmus Suonio
    (figgie.calibrate). Ce que montrent les journaux : ils montent leur offre d'achat d'un dollar à la
    fois au-dessus de la meilleure (et descendent leur vente de même), cotent sans cesse, et échangent
    surtout en fin de manche. Faite pour la règle du site (single_quote).

    Valeur d'une carte : base + goal_worth x P(couleur objectif), d'après ma donne et les cartes
    échangées. Je n'achète pas au-dessus de valeur - marge, je ne vends pas en dessous de valeur + marge,
    et la marge fond au fil de la manche (margin x temps restant ^ margin_power). Les bots du site ne
    sont pas d'accord entre eux (une carte bradée est presque toujours rachetée plus cher) : chaque valeur
    reçoit un écart tiré au hasard (écart-type `noise`), retiré après chaque échange. Et ils lisent le
    marché : sur le site, ce sont les plus hautes offres d'achat qui désignent l'objectif (d'après Rasmus
    Suonio). Une couleur où les autres ont proposé plus cher devient plus probablement l'objectif :
    poids exp(read x (plus haut prix proposé par les autres dans la couleur - moyenne sur les couleurs)).
    """
    name = "hard_simule"
    # Réglage de figgie.calibrate (resultats/phase5c/calibration_hard.md), sauf reaction, idle, start et open_bid.
    reaction, idle = 0.3, 0.5
    pace = 0.6         # secondes entre deux actions, en moyenne
    start = 5.0        # instant de ma première cotation
    base, goal_worth = 0, 30
    margin, margin_power = 6, 0.5
    open_bid, open_ask = 1, 20  # premiers prix, quand personne n'a encore coté
    noise = 6
    read = 0.05

    def __init__(self):
        self.next_time = 0.0
        self._offsets, self._n_trades = None, -1
        self._top, self._seen = dict.fromkeys(SUITS, 0), 0
        self._key, self._values = None, None

    def values(self, view):
        for _t, player, kind, suit, price in view.events[self._seen:]:
            if kind == "bid" and player != view.seat:
                self._top[suit] = max(self._top[suit], price)
        self._seen = len(view.events)
        key = (tuple(view.hand.values()), len(view.trades), tuple(self._top.values()))
        if key == self._key:
            return self._values
        mean_top = sum(self._top.values()) / len(SUITS)
        weights = {s: math.exp(self.read * (self._top[s] - mean_top)) for s in SUITS} if self.read else None
        p = goal_probabilities(view.hand, known_minimums(view.trades, view.n_players), view.seat, goal_weights=weights,
                               drawn=initial_hand(view.hand, view.trades, view.seat))
        self._key, self._values = key, {s: self.base + self.goal_worth * p[s] for s in SUITS}
        return self._values

    def act(self, view, rng):
        if view.time < max(self.start, self.next_time):
            return None
        if len(view.trades) != self._n_trades:
            self._offsets = {s: rng.gauss(0, self.noise) for s in SUITS}
            self._n_trades = len(view.trades)
        values = {s: v + self._offsets[s] for s, v in self.values(view).items()}
        m = self.margin * (1 - view.time / view.duration) ** self.margin_power
        suits = list(SUITS)
        rng.shuffle(suits)
        for s in suits:
            action = self._decide(view, s, floor(values[s] - m), max(1, ceil(values[s] + m)), rng)
            if action:
                self.next_time = view.time + rng.expovariate(1 / self.pace)
                return action
        return None

    def _decide(self, view, s, limit, floor_, rng):
        bid, ask = view.best(s, "bid"), view.best(s, "ask")
        mine_bid, mine_ask = view.mine(s, "bid"), view.mine(s, "ask")
        if (mine_bid is not None and mine_bid > limit) or (mine_ask is not None and mine_ask < floor_):
            return ("cancel", s)  # mon prix affiché ne me convient plus
        if ask and ask[0] <= limit and ask[0] <= view.cash:
            return ("buy", s, ask[0])
        if bid and bid[0] >= floor_ and view.hand[s] > 0:
            return ("sell", s, bid[0])
        options = []
        if mine_bid is None or (bid and bid[0] >= mine_bid):  # je ne suis pas le meilleur acheteur : je monte d'un dollar
            target = bid[0] + 1 if bid else self.open_bid
            if target <= min(limit, view.cash) and (not ask or target < ask[0]) and target < (mine_ask or 10**9):
                options.append(("bid", s, target))
        if (mine_ask is None or (ask and ask[0] <= mine_ask)) and view.hand[s] > 0:
            target = ask[0] - 1 if ask else max(self.open_ask, floor_)
            if target >= floor_ and (not bid or target > bid[0]) and target > (mine_bid or 0):
                options.append(("ask", s, target))
        return rng.choice(options) if options else None

class LeagueReaderBot(ReaderBot):
    """Phase 4. Le lecteur, avec un modèle de signaux réappris sur des parties de la ligue, où jouent
    aussi des lecteurs, des exploiteurs et des menteurs (figgie.learn --league), et un réglage choisi
    à 5 joueurs avec le test de minorité (figgie.tune --minority, resultats/phase4/)."""
    name = "lecteur_ligue"
    model_file = "signaux_ligue.json"
    spread, edge = 10, 3  # hors du zoo : pour les tests de robustesse

ZOO = {bot.name: bot for bot in (RandomBot, HeuristicBot, BayesBot, AggressiveBot, PassiveBot, SniperBot,
                                 MarginalBot, ReaderBot, ExploiterBot, ReaderExploiterBot)}
