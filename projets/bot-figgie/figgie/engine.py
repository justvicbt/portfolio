"""Moteur de Figgie : donne, carnet d'ordres, échanges et score.

Règles (figgie.com) :
- 4 ou 5 joueurs, 350 $ chacun, ante pour un pot de 200 $.
- 40 cartes : une couleur de 12, deux de 10, une de 8.
- La couleur objectif est la jumelle (même teinte) de la couleur de 12.
- Chaque carte objectif rapporte 10 $, le reste du pot va à la majorité.
- Un échange = une carte. Après chaque échange, toutes les cotations sont annulées.

Carnet : chaque joueur a au plus une offre d'achat et une offre de vente par couleur.
Prendre une cotation sert la meilleure d'abord, et à prix égal la plus ancienne.
"""
from dataclasses import dataclass
import heapq
import random

SUITS = ("S", "C", "H", "D")  # pique, trèfle, cœur, carreau
TWIN = {"S": "C", "C": "S", "H": "D", "D": "H"}
START_CASH = 350
POT = 200
GOAL_CARD_VALUE = 10


class IllegalAction(ValueError):
    """Action refusée par le moteur (pas la carte, pas l'argent, rien à prendre...)."""


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
    # shortcut: partage exact en float (33,33 $), l'arrondi de figgie.com n'est pas documenté.
    share = rest / len(winners)
    return [GOAL_CARD_VALUE * n + (share if i in winners else 0) for i, n in enumerate(goal_counts)]


def best_quote(book, suit, side, exclude=None):
    """Meilleure cotation (prix, joueur) d'un côté du carnet, en ignorant le joueur `exclude`.
    Offre d'achat : le prix le plus haut. Offre de vente : le plus bas. À prix égal, la plus ancienne."""
    quotes = [(price, seq, p) for p, (price, seq) in book[suit][side].items() if p != exclude]
    if not quotes:
        return None
    sign = -1 if side == "bid" else 1
    price, _, player = min(quotes, key=lambda q: (sign * q[0], q[1]))
    return price, player


def empty_book():
    return {s: {"bid": {}, "ask": {}} for s in SUITS}  # {joueur: (prix, numéro d'arrivée)}


class Market:
    """État d'une manche : argent, mains et carnet."""

    def __init__(self, hands):
        n = len(hands)
        self.hands = [dict(h) for h in hands]
        self.cash = [START_CASH - POT / n] * n
        self.book = empty_book()
        self.trades = []  # (acheteur, vendeur, couleur, prix)
        self._seq = 0

    def best(self, suit, side, exclude=None):
        return best_quote(self.book, suit, side, exclude)

    def apply(self, player, action):
        """Applique une action. Renvoie l'échange réalisé ou None. Lève IllegalAction si refusée.

        ("bid", couleur, prix)   propose d'acheter
        ("ask", couleur, prix)   propose de vendre
        ("buy", couleur, prix)   prend la meilleure vente, si elle coûte au plus `prix` (le prix que j'ai vu)
        ("sell", couleur, prix)  prend le meilleur achat, s'il rapporte au moins `prix`
        ("cancel", couleur)      retire mes cotations dans cette couleur

        Le prix d'une prise protège contre la latence : si le carnet a bougé avant que mon ordre
        arrive, il est refusé au lieu de s'exécuter à un prix que je n'ai pas vu.
        """
        if not isinstance(action, (tuple, list)) or len(action) < 2:
            raise IllegalAction(f"action mal formée : {action!r}")
        kind, suit = action[0], action[1]
        if suit not in SUITS:
            raise IllegalAction(f"couleur inconnue : {suit!r}")
        book = self.book[suit]
        if kind == "cancel":
            if player not in book["bid"] and player not in book["ask"]:
                raise IllegalAction("rien à annuler")
            book["bid"].pop(player, None)
            book["ask"].pop(player, None)
            return None
        if kind in ("bid", "ask", "buy", "sell"):
            price = action[2] if len(action) > 2 else None
            if not isinstance(price, int) or isinstance(price, bool) or price < 1:
                raise IllegalAction(f"prix invalide : {price!r}")
        if kind == "bid":
            if price > self.cash[player]:
                raise IllegalAction("pas assez d'argent")
            ask = self.best(suit, "ask", exclude=player)
            if ask and price >= ask[0]:  # l'offre croise une vente : échange au prix affiché
                return self._trade(buyer=player, seller=ask[1], suit=suit, price=ask[0])
            if player in book["ask"] and price >= book["ask"][player][0]:
                raise IllegalAction("une offre ne peut pas croiser ma propre vente")
            book["bid"][player] = (price, self._next_seq())
            return None
        if kind == "ask":
            if self.hands[player][suit] < 1:
                raise IllegalAction("pas de carte à vendre")
            bid = self.best(suit, "bid", exclude=player)
            if bid and price <= bid[0]:  # la vente croise une offre : échange au prix affiché
                return self._trade(buyer=bid[1], seller=player, suit=suit, price=bid[0])
            if player in book["bid"] and price <= book["bid"][player][0]:
                raise IllegalAction("une vente ne peut pas croiser ma propre offre")
            book["ask"][player] = (price, self._next_seq())
            return None
        if kind == "buy":
            ask = self.best(suit, "ask", exclude=player)
            if not ask or ask[0] > price:
                raise IllegalAction("aucune vente à prendre à ce prix")
            return self._trade(buyer=player, seller=ask[1], suit=suit, price=ask[0])
        if kind == "sell":
            bid = self.best(suit, "bid", exclude=player)
            if not bid or bid[0] < price:
                raise IllegalAction("aucune offre à prendre à ce prix")
            return self._trade(buyer=bid[1], seller=player, suit=suit, price=bid[0])
        raise IllegalAction(f"action inconnue : {kind!r}")

    def _next_seq(self):
        self._seq += 1
        return self._seq

    def _trade(self, buyer, seller, suit, price):
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
        self.book = empty_book()  # tout est annulé après un échange
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
    time: float
    duration: float

    def best(self, suit, side):
        """Meilleure cotation des autres joueurs : (prix, joueur) ou None."""
        return best_quote(self.book, suit, side, exclude=self.seat)

    def mine(self, suit, side):
        """Prix de ma propre cotation, ou None."""
        quote = self.book[suit][side].get(self.seat)
        return quote[0] if quote else None


@dataclass
class RoundResult:
    profits: list  # gain de chaque siège (argent final moins 350 $)
    log: dict      # journal complet, rejouable avec replay()


def _final_profits(market, goal):
    payouts = score([h[goal] for h in market.hands])
    return [c + p - START_CASH for c, p in zip(market.cash, payouts)]


def _view(market, seat, time, duration):
    return View(seat, len(market.hands), dict(market.hands[seat]), market.cash[seat],
                {s: {side: dict(q) for side, q in sides.items()} for s, sides in market.book.items()},
                list(market.trades), [sum(h.values()) for h in market.hands], time, duration)


LOG_FORMAT = 2  # 1 = phase 0 (ticks), 2 = phase 1 (temps continu, instant du regard, prix des prises)
DEFAULT_REACTION = 0.3  # secondes entre ce qu'un bot voit et l'arrivée de son action
DEFAULT_IDLE = 1.0      # secondes en moyenne avant de regarder à nouveau quand rien ne bouge


def play_round(bots, seed, duration=240.0):
    """Joue une manche en temps continu. `bots` : une classe (ou fabrique) de bot par siège.

    Chaque bot regarde le marché quand il change, ou de lui-même de temps en temps (attribut
    `idle`). Son action arrive `reaction` secondes plus tard (± 50 %), sur un marché qui a pu
    bouger entre-temps : le plus rapide prend la cotation, le plus lent voit son action refusée.
    """
    n = len(bots)
    if n not in (4, 5):
        raise ValueError("Figgie se joue à 4 ou 5 joueurs")
    hands, goal = deal(random.Random(seed), n)
    market = Market(hands)
    players = [make() for make in bots]
    bot_rngs = [random.Random(f"{seed}:bot:{i}") for i in range(n)]
    time_rngs = [random.Random(f"{seed}:time:{i}") for i in range(n)]
    reaction = [getattr(p, "reaction", DEFAULT_REACTION) for p in players]
    idle = [getattr(p, "idle", DEFAULT_IDLE) for p in players]
    if min(reaction) <= 0 or min(idle) <= 0:
        raise ValueError("reaction et idle doivent être > 0 (sinon la manche ne finit jamais)")

    events = []  # tas de (instant, numéro, siège, envoi) ; envoi None = le bot regarde, sinon (action, vue à)
    counter = 0
    next_look = [None] * n
    in_flight = [False] * n  # un bot a au plus une action en route

    def push(t, seat, sent=None):
        nonlocal counter
        counter += 1
        heapq.heappush(events, (t, counter, seat, sent))

    def look_at(seat, t):
        if not in_flight[seat] and (next_look[seat] is None or t < next_look[seat]):
            next_look[seat] = t
            push(t, seat)

    for seat in range(n):
        look_at(seat, time_rngs[seat].uniform(0, 0.5))  # tout le monde ne découvre pas sa main au même instant

    actions = []
    while events:
        t, _, seat, sent = heapq.heappop(events)
        if t >= duration:
            break
        if sent is None:  # le bot regarde
            if in_flight[seat] or next_look[seat] != t:
                continue  # regard périmé, remplacé par un plus récent
            next_look[seat] = None
            action = players[seat].act(_view(market, seat, t, duration), bot_rngs[seat])
            if action is None:
                look_at(seat, t + time_rngs[seat].expovariate(1 / idle[seat]))
            else:
                in_flight[seat] = True
                push(t + reaction[seat] * time_rngs[seat].uniform(0.5, 1.5), seat, (action, t))
            continue
        # l'action arrive au marché
        action, seen_at = sent
        in_flight[seat] = False
        try:
            market.apply(seat, action)
            ok = True
        except IllegalAction:
            ok = False  # une action refusée est ignorée mais gardée dans le journal
        actions.append([t, seat, list(action) if isinstance(action, (tuple, list)) else action, ok, seen_at])
        look_at(seat, t)
        if ok:
            for other in range(n):
                if other != seat:
                    look_at(other, t)  # le marché a changé : tout le monde le voit
    log = {
        "format": LOG_FORMAT, "seed": seed, "duration": duration, "bots": [getattr(p, "name", type(p).__name__) for p in players],
        "hands": hands, "goal": goal, "actions": actions,
    }
    profits = _final_profits(market, goal)
    log["profits"] = profits
    return RoundResult(profits, log)


def replay(log):
    """Rejoue un journal sans les bots et renvoie les gains. Lève ValueError si le journal est incohérent."""
    if log.get("format") != LOG_FORMAT:
        raise ValueError(f"format de journal {log.get('format')!r} inconnu (attendu : {LOG_FORMAT})")
    market = Market(log["hands"])
    for t, seat, action, ok, _seen_at in log["actions"]:
        try:
            market.apply(seat, action)
            accepted = True
        except IllegalAction:
            accepted = False
        if accepted != ok:
            raise ValueError(f"journal incohérent à t={t}, siège {seat} : {action}")
    return _final_profits(market, log["goal"])
