"""Seam « évaluation dupliquée » : rotation des sièges, intervalle de confiance et porte d'entrée."""
import unittest

from figgie.bots import RandomBot
from figgie.evaluate import duplicate_match, gate, mean_ci, zoo_report


class TestMeanCI(unittest.TestCase):
    def test_known_values(self):
        # moyenne 3, écart-type 1,5811, erreur type 0,7071, demi-largeur 1,96 × 0,7071 = 1,3859
        mean, low, high = mean_ci([1, 2, 3, 4, 5])
        self.assertAlmostEqual(mean, 3)
        self.assertAlmostEqual(low, 1.6141, places=4)
        self.assertAlmostEqual(high, 4.3859, places=4)


class TestDuplicateMatch(unittest.TestCase):
    def test_self_play_is_exactly_zero_on_every_deal(self):
        # Même bot partout : en passant par chaque siège, on additionne les gains de toute
        # la table, qui font zéro. Une rotation incomplète donnerait autre chose que zéro.
        for n in (4, 5):
            values = duplicate_match(RandomBot, RandomBot, n_deals=10, n_players=n, duration=30)
            self.assertEqual(len(values), 10)
            for v in values:
                self.assertAlmostEqual(v, 0, places=9)


class TestZooReport(unittest.TestCase):
    def test_candidate_never_faces_itself(self):
        from figgie.bots import PassiveBot
        report = zoo_report(PassiveBot, n_deals=2, duration=10)
        self.assertNotIn("passif", report)
        self.assertEqual(len(report), 5)


class TestGate(unittest.TestCase):
    def test_gate_does_not_apply_when_no_reference_is_in_the_report(self):
        self.assertIsNone(gate({"aleatoire": (5.0, 1.0, 9.0)}))

    def test_gate_requires_beating_heuristic_and_sniper(self):
        win, tie = (5.0, 1.0, 9.0), (5.0, -1.0, 11.0)
        self.assertTrue(gate({"heuristique": win, "sniper": win}))
        self.assertFalse(gate({"heuristique": win, "sniper": tie}))
        self.assertFalse(gate({"heuristique": tie, "sniper": win}))
        self.assertTrue(gate({"sniper": win}))  # le candidat est l'heuristique : seule l'autre référence compte

    def test_gate_requires_ci_above_zero_against_heuristic(self):
        self.assertTrue(gate({"heuristique": (5.0, 1.0, 9.0)}))
        self.assertFalse(gate({"heuristique": (5.0, -1.0, 11.0)}))


if __name__ == "__main__":
    unittest.main()
