"""Seam « évaluation dupliquée » : rotation des sièges, intervalle de confiance et porte d'entrée."""
import unittest

from figgie.bots import ZOO, RandomBot
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
        self.assertEqual(len(report), len(ZOO) - 1)


class TestGate(unittest.TestCase):
    def test_gate_does_not_apply_when_no_reference_is_in_the_report(self):
        self.assertIsNone(gate({"aleatoire": (5.0, 1.0, 9.0)}))

    def test_gate_requires_beating_heuristic_and_sniper(self):
        win, tie = (5.0, 1.0, 9.0), (5.0, -1.0, 11.0)
        self.assertTrue(gate({"heuristique": win, "sniper": win}))
        self.assertFalse(gate({"heuristique": win, "sniper": tie}))
        self.assertFalse(gate({"heuristique": tie, "sniper": win}))
        self.assertTrue(gate({"sniper": win}))  # le candidat est l'heuristique : seule l'autre référence compte

    def test_gate_also_requires_beating_the_previous_reference(self):
        win, tie = (5.0, 1.0, 9.0), (5.0, -1.0, 11.0)
        self.assertFalse(gate({"heuristique": win, "sniper": win, "bayesien": tie}))
        self.assertTrue(gate({"heuristique": win, "sniper": win, "bayesien": win, "marginal": win}))
        self.assertFalse(gate({"heuristique": win, "sniper": win, "bayesien": win, "marginal": tie}))

    def test_gate_refuses_a_bot_that_a_lone_opponent_exploits(self):
        # Test de minorité : chaque référence, seule face à des copies du candidat, ne doit pas gagner nettement.
        win = (5.0, 1.0, 9.0)
        report = {"heuristique": win, "sniper": win, "bayesien": win, "marginal": win}
        self.assertFalse(gate(report, minority={"marginal": (7.3, 6.0, 8.7)}))   # le marginal seul gagne : refusé
        self.assertTrue(gate(report, minority={"marginal": (0.5, -0.3, 1.3)}))   # pas nettement : accepté
        self.assertTrue(gate(report, minority={"marginal": (-4.0, -6.0, -2.0)}))

    def test_exploitation_counts_even_without_references(self):
        self.assertIs(gate({}, minority={"marginal": (7.3, 6.0, 8.7)}), False)

    def test_minority_report_puts_the_reference_alone(self):
        from figgie.bots import PassiveBot, SniperBot
        from figgie.evaluate import minority_report
        report = minority_report(PassiveBot, n_deals=2, references=("sniper",), duration=10)
        expected = mean_ci(duplicate_match(SniperBot, PassiveBot, n_deals=2, duration=10))
        self.assertEqual(report, {"sniper": expected})

    def test_gate_requires_ci_above_zero_against_heuristic(self):
        self.assertTrue(gate({"heuristique": (5.0, 1.0, 9.0)}))
        self.assertFalse(gate({"heuristique": (5.0, -1.0, 11.0)}))


if __name__ == "__main__":
    unittest.main()
