"""Seam « manche complète » : donne, score et conservation de l'argent."""
import math
import random
import unittest

from figgie.engine import TWIN, deal, play_round, score
from figgie.bots import ZOO, RandomBot


class TestDeal(unittest.TestCase):
    def test_deck_is_12_10_10_8_and_goal_is_twin_of_12(self):
        for seed in range(200):
            hands, goal = deal(random.Random(seed), n_players=4)
            totals = {s: sum(h[s] for h in hands) for s in hands[0]}
            self.assertEqual(sorted(totals.values()), [8, 10, 10, 12])
            twelve = next(s for s, n in totals.items() if n == 12)
            self.assertEqual(goal, TWIN[twelve])
            self.assertIn(totals[goal], (8, 10))

    def test_cards_per_player(self):
        for n, per_player in ((4, 10), (5, 8)):
            hands, _ = deal(random.Random(0), n_players=n)
            self.assertEqual([sum(h.values()) for h in hands], [per_player] * n)


class TestScore(unittest.TestCase):
    def test_single_majority_takes_rest_of_pot(self):
        # 10 cartes objectif : 10 $ chacune, il reste 100 $ pour la majorité.
        self.assertEqual(score([5, 3, 2, 0]), [150, 30, 20, 0])

    def test_tie_splits_rest_of_pot(self):
        self.assertEqual(score([4, 4, 2, 0]), [90, 90, 20, 0])

    def test_three_way_tie_with_8_goal_cards(self):
        # 8 cartes objectif : il reste 120 $, partagés en trois.
        self.assertEqual(score([2, 2, 2, 1, 1]), [60, 60, 60, 10, 10])


class TestPlayRound(unittest.TestCase):
    def test_money_is_conserved(self):
        for seed in range(30):
            for n in (4, 5):
                result = play_round([RandomBot] * n, seed=seed, ticks=60)
                self.assertTrue(math.isclose(sum(result.profits), 0, abs_tol=1e-9))

    def test_zoo_bots_only_play_legal_actions(self):
        for name, bot in ZOO.items():
            if name == "aleatoire":
                continue  # lui tente n'importe quoi, exprès
            for n in (4, 5):
                result = play_round([bot] * n, seed=11, ticks=100)
                refused = [a for a in result.log["actions"] if not a[3]]
                self.assertEqual(refused, [], name)
                self.assertTrue(math.isclose(sum(result.profits), 0, abs_tol=1e-9))

    def test_same_seed_same_round(self):
        a = play_round([RandomBot] * 4, seed=7, ticks=60)
        b = play_round([RandomBot] * 4, seed=7, ticks=60)
        self.assertEqual(a.profits, b.profits)


if __name__ == "__main__":
    unittest.main()
