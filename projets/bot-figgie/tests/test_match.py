"""Seam « parties multi-manches » : mémoire d'une manche à l'autre, révélation, tables mixtes."""
import math
import unittest

from figgie.bots import ZOO, RandomBot
from figgie.engine import play_match, play_round
from figgie.evaluate import duplicate_match


class Diary:
    """Note dans sa mémoire chaque révélation de fin de manche."""

    def act(self, view, rng):
        return None

    def end_round(self, reveal):
        self.memory.setdefault("reveals", []).append(reveal)


class TestPlayMatch(unittest.TestCase):
    def test_memory_survives_from_one_round_to_the_next(self):
        result = play_match([Diary, RandomBot, RandomBot, RandomBot], seed=3, rounds=4, duration=20)
        reveals = result.memories[0]["reveals"]
        self.assertEqual(len(reveals), 4)
        self.assertEqual([r["goal"] for r in reveals], [log["goal"] for log in result.logs])

    def test_reveal_shows_everyone_s_final_hand(self):
        result = play_match([Diary] + [ZOO["heuristique"]] * 3, seed=1, rounds=2, duration=30)
        for reveal in result.memories[0]["reveals"]:
            self.assertEqual(sum(sum(h.values()) for h in reveal["hands"]), 40)

    def test_rounds_use_different_deals(self):
        result = play_match([RandomBot] * 4, seed=2, rounds=3, duration=10)
        self.assertEqual(len({str(log["hands"]) for log in result.logs}), 3)

    def test_first_round_is_the_single_round_deal(self):
        # Une partie de N manches prolonge la manche isolée de même graine, au lieu d'en changer.
        single = play_round([RandomBot] * 4, seed=7, duration=10)
        match = play_match([RandomBot] * 4, seed=7, rounds=3, duration=10)
        self.assertEqual(match.logs[0]["hands"], single.log["hands"])

    def test_money_is_conserved_over_the_match(self):
        result = play_match([RandomBot] * 5, seed=4, rounds=3, duration=20)
        self.assertTrue(math.isclose(sum(result.profits), 0, abs_tol=1e-9))


class TestReaderMemory(unittest.TestCase):
    def test_reader_learns_who_to_trust_over_a_match(self):
        result = play_match([ZOO["lecteur"], RandomBot, ZOO["heuristique"], RandomBot], seed=5, rounds=3, duration=40)
        opponents = result.memories[0]["opponents"]
        self.assertEqual(sorted(opponents.count), [1, 2, 3])  # il a jugé chacun de ses adversaires
        self.assertNotIn(0, opponents.count)                   # mais pas lui-même


class TestDuplicateMatches(unittest.TestCase):
    def test_self_play_is_zero_with_several_rounds(self):
        values = duplicate_match(RandomBot, RandomBot, n_deals=3, rounds=3, duration=15)
        for v in values:
            self.assertAlmostEqual(v, 0, places=9)

    def test_mixed_table_self_play_is_zero(self):
        # Table mixte : le candidat tourne sur tous les sièges, les adversaires gardent leur ordre.
        values = duplicate_match(RandomBot, [RandomBot] * 3, n_deals=3, duration=15)
        for v in values:
            self.assertAlmostEqual(v, 0, places=9)

    def test_deals_can_be_split_into_chunks(self):
        # Couper les donnes en morceaux (pour les répartir sur plusieurs cœurs) ne change rien aux valeurs.
        whole = duplicate_match(RandomBot, ZOO["heuristique"], n_deals=4, duration=15)
        parts = duplicate_match(RandomBot, ZOO["heuristique"], n_deals=2, duration=15) + \
            duplicate_match(RandomBot, ZOO["heuristique"], n_deals=2, duration=15, first_deal=2)
        self.assertEqual(whole, parts)

    def test_mixed_table_runs(self):
        values = duplicate_match(ZOO["marginal"], [RandomBot, ZOO["heuristique"], ZOO["passif"]],
                                 n_deals=2, rounds=2, duration=15)
        self.assertEqual(len(values), 2)


if __name__ == "__main__":
    unittest.main()
