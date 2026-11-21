"""Seams « gain d'une carte », « comptage des cartes » et « valeur Monte Carlo »."""
import random
import unittest

from figgie.engine import SUITS, TWIN
from figgie.valuation import (card_gain, goal_probabilities, initial_hand, known_minimums, known_minimums_from_events,
                              marginal_values, sample_world)


def hand(**cards):
    h = dict.fromkeys(SUITS, 0)
    h.update(cards)
    return h


class TestCardGain(unittest.TestCase):
    # La carte change de main entre moi et un adversaire précis (le dernier argument).
    # Les nombres de cartes objectif couvrent tout le paquet : 10 cartes, il reste 100 $ pour la majorité.
    def test_breaking_a_tie_wins_the_whole_rest(self):
        # 3 contre 3 : 30 + 50 = 80 $. J'achète à l'autre meneur : 4 contre 2, 40 + 100 = 140 $.
        self.assertEqual(card_gain(3, [3, 2, 2], +1, counterparty=0), 60)

    def test_selling_to_the_leader_costs_more(self):
        # J'ai 4, le meneur adverse 3 : je touche 40 + 100 = 140 $.
        # Je vends au meneur : 3 contre 4, je ne touche plus que 30 $. Coût : 110 $.
        self.assertEqual(card_gain(4, [3, 2, 1], -1, counterparty=0), -110)
        # Je vends au joueur qui en a 1 : 3 contre 3, je touche 30 + 50 = 80 $. Coût : 60 $.
        self.assertEqual(card_gain(4, [3, 2, 1], -1, counterparty=2), -60)

    def test_buying_from_the_leader_is_worth_more(self):
        # 4 contre 5 : 40 $. J'achète au meneur : 5 contre 4, 50 + 100 = 150 $ (+110 $).
        self.assertEqual(card_gain(4, [5, 1, 0], +1, counterparty=0), 110)
        # J'achète à un autre : 5 contre 5, 50 + 50 = 100 $ (+60 $).
        self.assertEqual(card_gain(4, [5, 1, 0], +1, counterparty=1), 60)

    def test_card_without_majority_change_is_worth_10(self):
        self.assertEqual(card_gain(1, [5, 2, 2], +1, counterparty=1), 10)

    def test_eight_goal_cards_leave_120(self):
        # 8 cartes objectif, égalité à quatre à 2 : 20 + 30 = 50 $. J'en achète une : 3 contre 2, 30 + 120 = 150 $.
        self.assertEqual(card_gain(2, [2, 2, 2], +1, counterparty=0), 100)


class TestKnownMinimums(unittest.TestCase):
    def test_minimums_follow_the_public_trades(self):
        trades = [(1, 2, "H", 5), (1, 3, "H", 4), (2, 1, "H", 6), (3, 0, "S", 2)]
        mins = known_minimums(trades, n_players=4)
        self.assertEqual(mins[0], hand())       # a vendu un pique qu'on ne lui connaissait pas
        self.assertEqual(mins[1], hand(H=1))    # 2 cœurs achetés, 1 revendu
        self.assertEqual(mins[2], hand(H=1))    # a vendu un cœur inconnu, puis en a racheté un
        self.assertEqual(mins[3], hand(S=1))

    def test_an_ask_proves_the_card_is_held(self):
        # L'exemple de KnifeEdge (fil Reddit r/quant), à 5 joueurs. J'ai 5 trèfles.
        feed = [
            (1.0, 1, "ask", "C", 9),      # A propose un trèfle : il en a au moins un
            (2.0, 2, "bought", "C", 9),   # B le lui achète
            (2.0, 1, "sold", "C", 9),
            (3.0, 3, "ask", "C", 8),      # C propose un trèfle
            (4.0, 1, "ask", "C", 7),      # A en propose un autre
            (4.5, 1, "cancel", "C", 0),   # et l'annule : il l'avait quand même
            (5.0, 4, "bid", "C", 3),      # une offre d'achat ne prouve rien
            (6.0, 2, "bought", "C", 6),   # D vend un trèfle à B
            (6.0, 4, "sold", "C", 6),
        ]
        mins = known_minimums_from_events(feed, n_players=5)
        self.assertEqual([m["C"] for m in mins], [0, 1, 2, 1, 0])
        self.assertEqual(5 + sum(m["C"] for m in mins[1:]), 9)  # au moins 9 trèfles, donc 10 ou 12

    def test_without_asks_events_give_the_same_minimums_as_trades(self):
        trades = [(1, 2, "H", 5), (1, 3, "H", 4), (2, 1, "H", 6), (3, 0, "S", 2)]
        feed = [e for i, (b, s, suit, p) in enumerate(trades)
                for e in ((float(i), b, "bought", suit, p), (float(i), s, "sold", suit, p))]
        self.assertEqual(known_minimums_from_events(feed, 4), known_minimums(trades, 4))


class TestMonteCarlo(unittest.TestCase):
    def test_without_trades_probabilities_match_a_known_value(self):
        # Valeurs calculées en phase 0 : 6 piques en main donnent 60,9 % au trèfle.
        got = goal_probabilities(hand(S=6, C=1, H=2, D=1), [hand()] * 4, seat=0)
        self.assertAlmostEqual(got["C"], 0.6091, places=4)
        self.assertAlmostEqual(got["S"], 0.1163, places=4)
        self.assertAlmostEqual(sum(got.values()), 1)

    def test_bought_cards_are_a_constraint_not_a_draw(self):
        # Un adversaire qui a acheté 4 trèfles les a choisis : ce n'est pas un tirage au hasard.
        # Avec drawn (ma donne, seul vrai tirage), ces cartes ne servent qu'à exclure les paquets impossibles.
        h = hand(S=1, C=3, H=3, D=3)
        mins = [hand(), hand(C=4), hand(), hand()]
        free = goal_probabilities(h, [hand()] * 4, seat=0)
        got = goal_probabilities(h, mins, seat=0, drawn=h)
        for s in SUITS:
            self.assertAlmostEqual(got[s], free[s])  # 7 trèfles connus : possible dans tous les paquets
        mins = [hand(), hand(C=8), hand(), hand()]  # 11 trèfles connus : seul un paquet à 12 trèfles convient
        self.assertAlmostEqual(goal_probabilities(h, mins, seat=0, drawn=h)["S"], 1.0)

    def test_initial_hand_undoes_my_trades(self):
        trades = [(0, 1, "H", 5), (2, 0, "S", 3), (0, 3, "H", 4)]  # j'achète 2 cœurs et vends 1 pique
        self.assertEqual(initial_hand(hand(S=1, C=2, H=5, D=2), trades, seat=0), hand(S=2, C=2, H=3, D=2))

    def test_market_weights_multiply_the_probabilities(self):
        # Le marché rend le cœur deux fois plus probable : P(trèfle) = 0,6091 / (1 + 0,1163) = 0,5456.
        weights = {"S": 1, "C": 1, "H": 2, "D": 1}
        got = goal_probabilities(hand(S=6, C=1, H=2, D=1), [hand()] * 4, seat=0, goal_weights=weights)
        self.assertAlmostEqual(got["C"], 0.5456, places=4)
        self.assertAlmostEqual(got["H"], 2 * 0.1163 / 1.1163, places=3)

    def test_marginal_values_follow_the_market_weights(self):
        # Si le marché désigne presque sûrement le carreau, acheter du carreau vaut plus que du trèfle.
        h = hand(S=6, C=1, H=2, D=1)
        weights = {"S": 0.01, "C": 0.01, "H": 0.01, "D": 1}
        values = marginal_values(h, 0, [10] * 4, [hand()] * 4, random.Random(2), samples=400, goal_weights=weights)
        self.assertGreater(min(values["D"][0].values()), min(values["C"][0].values()))

    def test_known_cards_shift_the_probabilities(self):
        # Si un adversaire a acheté 4 trèfles, les trèfles sont plus nombreux : le pique (leur jumeau) devient plus probable.
        h = hand(S=1, C=3, H=3, D=3)
        before = goal_probabilities(h, [hand()] * 4, seat=0)
        after = goal_probabilities(h, [hand(), hand(C=4), hand(), hand()], seat=0)
        self.assertGreater(after["S"], before["S"])

    def test_sampled_worlds_respect_what_i_know(self):
        rng = random.Random(0)
        h = hand(S=3, C=2, H=3, D=2)
        counts = [10, 12, 9, 9]
        mins = [hand(), hand(H=2), hand(), hand(D=1)]
        for _ in range(300):
            goal, hands = sample_world(h, 0, counts, mins, rng)
            self.assertEqual(hands[0], h)
            for j in range(4):
                self.assertEqual(sum(hands[j].values()), counts[j])
                for s in SUITS:
                    self.assertGreaterEqual(hands[j][s], mins[j][s])
            totals = sorted(sum(x[s] for x in hands) for s in SUITS)
            self.assertEqual(totals, [8, 10, 10, 12])
            twelve = next(s for s in SUITS if sum(x[s] for x in hands) == 12)
            self.assertEqual(goal, TWIN[twelve])

    def test_marginal_values_match_the_full_sampler(self):
        # La version rapide ne tire que les cartes objectif ; elle doit donner les mêmes valeurs
        # que la moyenne calculée à la main sur des mondes complets.
        h = hand(S=2, C=3, H=4, D=1)
        counts, mins = [10, 11, 9, 10], [hand(), hand(H=2), hand(), hand(C=1)]
        rng = random.Random(5)
        n = 4000
        buy_sum = {s: {j: 0.0 for j in (1, 2, 3)} for s in SUITS}
        buy_worlds = {s: {j: n for j in (1, 2, 3)} for s in SUITS}
        sell = {s: {j: 0.0 for j in (1, 2, 3)} for s in SUITS}
        for _ in range(n):
            goal, hands = sample_world(h, 0, counts, mins, rng)
            others = [x[goal] for x in hands[1:]]
            for k, j in enumerate((1, 2, 3)):
                if others[k] > 0:
                    buy_sum[goal][j] += card_gain(h[goal], others, +1, k)
                else:
                    buy_worlds[goal][j] -= 1  # monde impossible s'il me vend une carte objectif
                sell[goal][j] -= card_gain(h[goal], others, -1, k) / n
        ref = {s: ({j: buy_sum[s][j] / buy_worlds[s][j] for j in (1, 2, 3)}, sell[s]) for s in SUITS}
        fast = marginal_values(h, 0, counts, mins, random.Random(6), samples=n)
        for s in SUITS:
            for j in (1, 2, 3):
                self.assertAlmostEqual(fast[s][0][j], ref[s][0][j], delta=1.5, msg=(s, j))
                self.assertAlmostEqual(fast[s][1][j], ref[s][1][j], delta=1.5, msg=(s, j))

    def test_marginal_values_are_sensible(self):
        rng = random.Random(1)
        h = hand(S=6, C=1, H=2, D=1)  # le trèfle (jumeau du pique) est probablement l'objectif
        values = marginal_values(h, 0, [10] * 4, [hand()] * 4, rng, samples=400)
        cheapest_buy = {s: min(values[s][0].values()) for s in SUITS}
        self.assertGreater(cheapest_buy["C"], cheapest_buy["H"])
        self.assertGreater(cheapest_buy["C"], cheapest_buy["D"])
        for s in SUITS:
            for side in values[s]:
                self.assertEqual(sorted(side), [1, 2, 3])
                self.assertTrue(all(-130 <= v <= 130 for v in side.values()))


if __name__ == "__main__":
    unittest.main()
