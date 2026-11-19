"""Seam « manche complète » : donne, score, conservation de l'argent et temps continu."""
import math
import random
import unittest

from figgie.engine import SUITS, TWIN, deal, play_round, score
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


class Seller:
    """Affiche une carte à 1 $ dès le début, une seule fois."""
    reaction, idle = 0.05, 1000
    done = False

    def act(self, view, rng):
        if self.done:
            return None
        self.done = True
        return ("ask", next(s for s in SUITS if view.hand[s] > 0), 1)


class Buyer:
    """Achète tout ce qui est affiché."""
    idle = 1000

    def __init__(self, reaction):
        self.reaction = reaction

    def act(self, view, rng):
        return next((("buy", s, view.best(s, "ask")[0]) for s in SUITS if view.best(s, "ask")), None)


class Idle:
    def act(self, view, rng):
        return None


class TestPlayRound(unittest.TestCase):
    def test_money_is_conserved(self):
        for seed in range(30):
            for n in (4, 5):
                result = play_round([RandomBot] * n, seed=seed, duration=30)
                self.assertTrue(math.isclose(sum(result.profits), 0, abs_tol=1e-9))

    def test_zoo_bots_are_only_refused_when_the_market_moved(self):
        # Avec la latence, une action peut arriver sur un marché qui a changé. Un bot du zoo
        # ne doit être refusé que pour ça : un autre joueur a agi entre son regard et l'arrivée.
        for name, bot in ZOO.items():
            if name == "aleatoire":
                continue  # lui tente n'importe quoi, exprès
            for n in (4, 5):
                result = play_round([bot] * n, seed=11, duration=60)
                changes = []  # (instant, siège) de chaque action acceptée
                for t, seat, action, ok, seen_at in result.log["actions"]:
                    if not ok:
                        moved = any(seen_at <= tc <= t and sc != seat for tc, sc in changes)
                        self.assertTrue(moved, (name, t, action))
                    else:
                        changes.append((t, seat))
                self.assertTrue(math.isclose(sum(result.profits), 0, abs_tol=1e-9))

    def test_actions_happen_within_the_round(self):
        result = play_round([RandomBot] * 4, seed=2, duration=20)
        times = [a[0] for a in result.log["actions"]]
        self.assertTrue(times)
        self.assertTrue(all(0 <= t < 20 for t in times))
        self.assertEqual(times, sorted(times))

    def test_faster_player_wins_the_race(self):
        for seed in range(10):
            bots = [Seller, lambda: Buyer(0.5), lambda: Buyer(0.1), Idle]
            result = play_round(bots, seed=seed, duration=5)
            trades = [a for a in result.log["actions"] if a[3] and a[2][0] == "buy"]
            self.assertEqual(trades[0][1], 2, seed)  # le siège 2 réagit en 0,1 s
            refused = [a for a in result.log["actions"] if not a[3]]
            self.assertTrue(any(a[1] == 1 for a in refused))  # le lent arrive après la bataille

    def test_same_seed_same_round(self):
        a = play_round([RandomBot] * 4, seed=7, duration=30)
        b = play_round([RandomBot] * 4, seed=7, duration=30)
        self.assertEqual(a.log, b.log)


if __name__ == "__main__":
    unittest.main()
