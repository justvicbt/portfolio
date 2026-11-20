"""Ce que vaut vraiment une carte : comptage des cartes et valeur marginale par Monte Carlo.

Une carte objectif rapporte 10 $, mais elle peut aussi me faire gagner (ou perdre) la majorité,
qui vaut 100 ou 120 $. Sa valeur dépend donc de combien j'en ai et de combien en ont les autres.
On ne connaît pas leurs mains : on en tire au hasard des milliers de versions compatibles avec
ce que l'on sait, et on fait la moyenne. C'est la méthode de Monte Carlo.
"""
from functools import lru_cache
from math import comb

from figgie.engine import SUITS, TWIN, payout

# Les 12 compositions possibles du paquet : (couleur de 12, couleur de 8, taille de chaque couleur).
CONFIGS = [
    (twelve, eight, {s: 12 if s == twelve else 8 if s == eight else 10 for s in SUITS})
    for twelve in SUITS for eight in SUITS if eight != twelve
]


def card_gain(mine, others, delta, counterparty):
    """Variation de mon gain final quand une carte objectif change de main entre moi et
    l'adversaire `counterparty` (indice dans `others`) : +1 si je la reçois, -1 si je la donne.

    La carte quitte une main pour en rejoindre une autre : vendre au meneur peut lui offrir
    la majorité, acheter au meneur peut la lui reprendre. C'est pour ça que le joueur d'en face compte.
    """
    return _card_gain(mine, tuple(others), delta, counterparty)


@lru_cache(maxsize=None)
def _card_gain(mine, others, delta, counterparty):
    # Les mêmes situations reviennent des millions de fois : on garde chaque résultat (calcul exact, inchangé).
    after = list(others)
    after[counterparty] -= delta
    return payout(mine + delta, after) - payout(mine, list(others))


def known_minimums(trades, n_players):
    """Minimum de cartes que chaque joueur détient dans chaque couleur, d'après les échanges publics.

    Un achat ajoute une carte connue. Une vente en retire une, mais seulement si on lui en
    connaissait une : sinon c'est une carte de sa donne, qu'on ne connaissait pas.
    """
    mins = [dict.fromkeys(SUITS, 0) for _ in range(n_players)]
    for buyer, seller, suit, _price in trades:
        mins[buyer][suit] += 1
        mins[seller][suit] = max(0, mins[seller][suit] - 1)
    return mins


def _known_cards(hand, seat, minimums):
    return {s: hand[s] + sum(m[s] for j, m in enumerate(minimums) if j != seat) for s in SUITS}


def _config_weights(known, goal_weights=None, drawn=None):
    """Poids de chaque composition du paquet, multiplié par ce que le marché dit de sa couleur objectif
    (`goal_weights`, 1 partout par défaut).

    Sans `drawn` (phase 2) : nombre de façons d'y trouver toutes les cartes que je connais, comme si
    elles avaient été tirées au hasard. Or les cartes achetées ont été choisies, pas tirées : ce
    calcul rend le bot trop sûr de lui. Avec `drawn` (ma donne, le seul vrai tirage, phase 3) : seule
    ma donne compte comme tirage, et les cartes connues servent à exclure les paquets impossibles.
    """
    weights = []
    for twelve, _eight, sizes in CONFIGS:
        w = goal_weights[TWIN[twelve]] if goal_weights else 1
        for s in SUITS:
            if drawn is None:
                w *= comb(sizes[s], known[s])  # vaut 0 si je connais plus de cartes que la couleur n'en a
            else:
                w *= comb(sizes[s], drawn[s]) if sizes[s] >= known[s] else 0
        weights.append(w)
    return weights


def initial_hand(hand, trades, seat):
    """Ma donne de départ : ma main actuelle, moins ce que j'ai acheté, plus ce que j'ai vendu."""
    h = dict(hand)
    for buyer, seller, suit, _price in trades:
        h[suit] += (seller == seat) - (buyer == seat)
    return h


def goal_probabilities(hand, minimums, seat, goal_weights=None, drawn=None):
    """P(couleur objectif = s) sachant ma main, les cartes connues des autres et, si fourni, le marché.
    `drawn` : ma donne de départ, pour ne compter que le vrai tirage (voir _config_weights)."""
    weights = _config_weights(_known_cards(hand, seat, minimums), goal_weights, drawn)
    probs = dict.fromkeys(SUITS, 0.0)
    for (twelve, _eight, _sizes), w in zip(CONFIGS, weights):
        probs[TWIN[twelve]] += w
    total = sum(weights)
    return {s: p / total for s, p in probs.items()}


def sample_world(hand, seat, card_counts, minimums, rng):
    """Tire une version possible de la table : (couleur objectif, main de chaque joueur).
    Version complète et lisible de l'algorithme ; marginal_values en utilise une version rapide,
    et les tests vérifient que les deux donnent les mêmes valeurs.

    1. On tire la composition du paquet selon sa probabilité.
    2. Les cartes qu'on ne sait pas placer sont mélangées et distribuées dans les places
       inconnues de chaque adversaire (son nombre de cartes moins ce qu'on lui connaît).
    """
    known = _known_cards(hand, seat, minimums)
    twelve, _eight, sizes = rng.choices(CONFIGS, weights=_config_weights(known))[0]
    pool = [s for s in SUITS for _ in range(sizes[s] - known[s])]
    rng.shuffle(pool)
    hands, i = [], 0
    for j, count in enumerate(card_counts):
        if j == seat:
            hands.append(dict(hand))
            continue
        h = dict(minimums[j])
        for s in pool[i:i + count - sum(h.values())]:
            h[s] += 1
        i += count - sum(minimums[j].values())
        hands.append(h)
    assert i == len(pool), "les nombres de cartes ne collent pas avec le paquet"
    return TWIN[twelve], hands


def marginal_values(hand, seat, card_counts, minimums, rng, samples=300, goal_weights=None, drawn=None):
    """Valeur d'une carte de chaque couleur selon le joueur d'en face.

    Renvoie {couleur: (achat, vente)} où achat = {siège: ce que me rapporte une carte achetée à ce joueur}
    et vente = {siège: ce que me coûte une carte vendue à ce joueur}.
    """
    # Même tirage que sample_world, mais on ne place que les cartes objectif : ce sont les seules
    # qui comptent pour le gain, et c'est beaucoup plus rapide que de distribuer toute la table.
    known = _known_cards(hand, seat, minimums)
    opponents = [j for j in range(len(card_counts)) if j != seat]
    slot_owner = []  # pour chaque place inconnue chez les adversaires : à qui elle appartient
    for k, j in enumerate(opponents):
        slot_owner += [k] * (card_counts[j] - sum(minimums[j].values()))
    slots = range(len(slot_owner))
    buy = {s: [0.0] * len(opponents) for s in SUITS}
    buy_worlds = {s: [samples] * len(opponents) for s in SUITS}
    sell = {s: [0.0] * len(opponents) for s in SUITS}
    for twelve, _eight, sizes in rng.choices(CONFIGS, weights=_config_weights(known, goal_weights, drawn), k=samples):
        goal = TWIN[twelve]
        others = [minimums[j][goal] for j in opponents]
        for slot in rng.sample(slots, sizes[goal] - known[goal]):
            others[slot_owner[slot]] += 1
        mine = hand[goal]
        others = tuple(others)
        for k in range(len(opponents)):
            if others[k] > 0:
                buy[goal][k] += _card_gain(mine, others, +1, k)
            else:
                buy_worlds[goal][k] -= 1  # monde impossible si ce joueur me vend une carte objectif
            if mine > 0:
                sell[goal][k] -= _card_gain(mine, others, -1, k)
    return {
        s: ({j: buy[s][k] / max(1, buy_worlds[s][k]) for k, j in enumerate(opponents)},
            {j: sell[s][k] / samples for k, j in enumerate(opponents)})
        for s in SUITS
    }
