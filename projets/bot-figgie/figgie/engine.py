"""Moteur de Figgie : donne, carnet d'ordres, échanges et score.

Règles (figgie.com) :
- 4 ou 5 joueurs, 350 $ chacun, ante pour un pot de 200 $.
- 40 cartes : une couleur de 12, deux de 10, une de 8.
- La couleur objectif est la jumelle (même teinte) de la couleur de 12.
- Chaque carte objectif rapporte 10 $, le reste du pot va à la majorité.
- Un échange = une carte. Après chaque échange, toutes les cotations sont annulées.

Le temps est découpé en `ticks` : à chaque tick, chaque joueur agit une fois,
dans un ordre tiré au hasard. (Phase 1 : temps continu.)
"""
from dataclasses import dataclass
import random

SUITS = ("S", "C", "H", "D")  # pique, trèfle, cœur, carreau
TWIN = {"S": "C", "C": "S", "H": "D", "D": "H"}
START_CASH = 350
POT = 200
GOAL_CARD_VALUE = 10


class IllegalAction(ValueError):
    """Action refusée par le moteur (pas la carte, pas l'argent, cotation pas meilleure...)."""


def deal(rng, n_players):
    """Tire la composition du paquet, mélange et distribue. Renvoie (mains, couleur objectif)."""
    twelve = rng.choice(SUITS)
    eight = rng.choice([s for s in SUITS if s != twelve])
    sizes = {s: 12 if s == twelve else 8 if s == eight else 10 for s in SUITS}
    deck = [s for s in SUITS for _ in range(sizes[s])]
    rng.shuffle(deck)
    per_player = len(deck) // n_players
    hands = []
    for p in range(n_players):
        cards = deck[p * per_player:(p + 1) * per_player]
        hands.append({s: cards.count(s) for s in SUITS})
    return hands, TWIN[twelve]


def score(goal_counts):
    """Gain de fin de manche de chaque joueur, à partir de son nombre de cartes objectif."""
    rest = POT - GOAL_CARD_VALUE * sum(goal_counts)
    best = max(goal_counts)
    winners = [i for i, n in enumerate(goal_counts) if n == best]
    # shortcut: partage exact en float (33,33 $), figgie.com arrondit peut-être ; à vérifier en phase 1.
    share = rest / len(winners)
    return [GOAL_CARD_VALUE * n + (share if i in winners else 0) for i, n in enumerate(goal_counts)]


class Market:
    """État d'une manche : argent, mains et carnet (meilleure offre et meilleure demande par couleur)."""

    def __init__(self, hands):
        n = len(hands)
        self.hands = [dict(h) for h in hands]
        self.cash = [START_CASH - POT / n] * n
        self.book = {s: {"bid": None, "ask": None} for s in SUITS}  # (prix, joueur)
        self.trades = []  # (acheteur, vendeur, couleur, prix)

    def apply(self, player, action):
        """Applique une action. Renvoie l'échange réalisé ou None. Lève IllegalAction si refusée."""
        if not isinstance(action, (tuple, list)) or len(action) < 2:
            raise IllegalAction(f"action mal formée : {action!r}")
        kind, suit = action[0], action[1] if len(action) > 1 else None
        if suit not in SUITS:
            raise IllegalAction(f"couleur inconnue : {suit!r}")
        quote = self.book[suit]
        if kind in ("bid", "ask"):
            price = action[2] if len(action) > 2 else None
            if not isinstance(price, int) or isinstance(price, bool) or price < 1:
                raise IllegalAction(f"prix invalide : {price!r}")
        if kind == "bid":
            if price > self.cash[player]:
                raise IllegalAction("pas assez d'argent")
            if quote["ask"] and price >= quote["ask"][0]:  # l'offre croise la demande : échange au prix affiché
                return self.apply(player, ("buy", suit))
            if quote["bid"] and price <= quote["bid"][0]:
                raise IllegalAction("une offre doit battre la meilleure offre")
            quote["bid"] = (price, player)
            return None
        if kind == "ask":
            if self.hands[player][suit] < 1:
                raise IllegalAction("pas de carte à vendre")
            if quote["bid"] and price <= quote["bid"][0]:  # la demande croise l'offre : échange au prix affiché
                return self.apply(player, ("sell", suit))
            if quote["ask"] and price >= quote["ask"][0]:
                raise IllegalAction("une demande doit battre la meilleure demande")
            quote["ask"] = (price, player)
            return None
        if kind == "buy":
            if not quote["ask"]:
                raise IllegalAction("aucune demande à prendre")
            price, seller = quote["ask"]
            return self._trade(buyer=player, seller=seller, suit=suit, price=price)
        if kind == "sell":
            if not quote["bid"]:
                raise IllegalAction("aucune offre à prendre")
            price, buyer = quote["bid"]
            return self._trade(buyer=buyer, seller=player, suit=suit, price=price)
        raise IllegalAction(f"action inconnue : {kind!r}")

    def _trade(self, buyer, seller, suit, price):
        if buyer == seller:
            raise IllegalAction("on ne traite pas avec soi-même")
        if self.cash[buyer] < price:
            raise IllegalAction("pas assez d'argent")
        if self.hands[seller][suit] < 1:
            raise IllegalAction("pas de carte à vendre")
        self.cash[buyer] -= price
        self.cash[seller] += price
        self.hands[buyer][suit] += 1
        self.hands[seller][suit] -= 1
        trade = (buyer, seller, suit, price)
        self.trades.append(trade)
        self.book = {s: {"bid": None, "ask": None} for s in SUITS}  # tout est annulé après un échange
        return trade


@dataclass
class View:
    """Ce qu'un joueur a le droit de voir. Les mains des autres restent cachées, seul leur nombre de cartes est public."""
    seat: int
    n_players: int
    hand: dict
    cash: float
    book: dict
    trades: list
    card_counts: list
    tick: int
    ticks: int


@dataclass
class RoundResult:
    profits: list  # gain de chaque siège (argent final moins 350 $)
    log: dict      # journal complet, rejouable avec replay()


def _final_profits(market, goal):
    payouts = score([h[goal] for h in market.hands])
    return [c + p - START_CASH for c, p in zip(market.cash, payouts)]


def play_round(bots, seed, ticks=200):
    """Joue une manche. `bots` : une classe (ou fabrique) de bot par siège."""
    n = len(bots)
    if n not in (4, 5):
        raise ValueError("Figgie se joue à 4 ou 5 joueurs")
    hands, goal = deal(random.Random(seed), n)
    market = Market(hands)
    players = [make() for make in bots]
    bot_rngs = [random.Random(f"{seed}:bot:{i}") for i in range(n)]
    order_rng = random.Random(f"{seed}:order")
    actions = []
    for tick in range(ticks):
        order = list(range(n))
        order_rng.shuffle(order)
        for seat in order:
            view = View(seat, n, dict(market.hands[seat]), market.cash[seat],
                        {s: dict(q) for s, q in market.book.items()}, list(market.trades),
                        [sum(h.values()) for h in market.hands], tick, ticks)
            action = players[seat].act(view, bot_rngs[seat])
            if action is None:
                continue
            try:
                market.apply(seat, action)
                ok = True
            except IllegalAction:
                ok = False  # une action refusée est ignorée mais gardée dans le journal
            actions.append([tick, seat, list(action), ok])
    log = {
        "seed": seed, "ticks": ticks, "bots": [getattr(p, "name", type(p).__name__) for p in players],
        "hands": hands, "goal": goal, "actions": actions,
    }
    profits = _final_profits(market, goal)
    log["profits"] = profits
    return RoundResult(profits, log)


def replay(log):
    """Rejoue un journal sans les bots et renvoie les gains. Lève ValueError si le journal est incohérent."""
    market = Market(log["hands"])
    for tick, seat, action, ok in log["actions"]:
        try:
            market.apply(seat, action)
            accepted = True
        except IllegalAction:
            accepted = False
        if accepted != ok:
            raise ValueError(f"journal incohérent au tick {tick}, siège {seat} : {action}")
    return _final_profits(market, log["goal"])
