"""Seam « prix selon le temps restant » (phase 5b) : les cotations d'un bot en début et en fin de manche."""
import unittest

from figgie.bots import HeuristicBot, IdleBot
from figgie.engine import play_round


def quotes(bot, seed=3):
    """Les cotations du siège 0, face à trois joueurs inactifs : (instant, côté, prix)."""
    result = play_round([bot, IdleBot, IdleBot, IdleBot], seed=seed)
    return [(t, kind, price) for t, seat, kind, _suit, price in result.events if seat == 0 and kind in ("bid", "ask")]


class TestSpreadOverTime(unittest.TestCase):
    def test_the_spread_narrows_from_its_start_value_to_its_late_value(self):
        # L'heuristique donne 12 $ à une couleur et 0 $ aux autres. Spread de 8 $ au début, 2 $ à la fin,
        # en ligne droite : 7,5 $ à t = 20 s, moins de 3 $ après t = 200 s. Le bot ne recote que quand
        # son prix arrondi change : sa dernière offre (9 $) part peu après 200 s, puis reste affichée.
        patient = type("Patient", (HeuristicBot,), {"spread": 8, "spread_late": 2, "edge": None})
        q = quotes(patient)
        early = [(k, p) for t, k, p in q if t < 20]
        late = [(k, p) for t, k, p in q if t >= 200]
        self.assertEqual(max(p for k, p in early if k == "bid"), 4)   # 12 - 8 au début
        self.assertEqual(max(p for k, p in late if k == "bid"), 9)    # 12 - 2,9 arrondi vers le bas
        self.assertEqual(min(p for k, p in early if k == "ask"), 8)   # 0 + 8 au début
        self.assertLessEqual(min(p for k, p in late if k == "ask"), 3)

    def test_without_a_late_value_the_spread_stays_fixed(self):
        fixed = type("Fixed", (HeuristicBot,), {"spread": 8, "edge": None})
        q = quotes(fixed)
        self.assertEqual(max(p for t, k, p in q if k == "bid"), 4)  # sur toute la manche


if __name__ == "__main__":
    unittest.main()
