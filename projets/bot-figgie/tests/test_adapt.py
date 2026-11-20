"""Seams « profil de table », « plus proches voisins », « bot adaptatif » et « évaluation multi-manches »."""
import unittest

from figgie.adapt import DEFAULT_ARM, AdaptiveBot, Neighbors, table_profile
from figgie.bots import ZOO, RandomBot
from figgie.engine import play_match
from figgie.evaluate import duplicate_match

# Un fil écrit à la main, sur une manche de 60 s. Je suis le joueur 0.
FEED = [
    (1.0, 1, "bid", "H", 5),
    (2.0, 1, "ask", "H", 9),       # le joueur 1 cote des deux côtés du cœur : écart de 4 $
    (3.0, 2, "bid", "S", 3),
    (4.0, 2, "bought", "S", 3),    # le joueur 3 vend un pique au joueur 2 : le carnet est vidé
    (4.0, 3, "sold", "S", 3),
    (5.0, 1, "bid", "H", 6),       # le joueur 1 recote 1 s après l'échange
    (6.5, 2, "bid", "S", 2),       # le joueur 2, 2,5 s après
    (7.0, 0, "bid", "C", 4),       # moi : ignoré
]


class TestTableProfile(unittest.TestCase):
    def test_profile_of_a_hand_written_feed(self):
        p = table_profile(FEED, me=0, duration=60)
        self.assertAlmostEqual(p["quote_rate_mean"], (3 + 2 + 0) / 3)  # cotations par minute : 3, 2 et 0
        self.assertAlmostEqual(p["quote_rate_max"], 3)
        self.assertAlmostEqual(p["spread_min"], 4)
        self.assertAlmostEqual(p["latency_min"], 1.0)
        self.assertAlmostEqual(p["silent_share"], 1 / 3)               # le joueur 3 n'a jamais coté


    def test_a_cancelled_quote_is_not_paired_with_a_later_one(self):
        # Le joueur 1 propose 5 $, annule, puis propose de vendre à 30 $ : il n'a jamais coté les deux côtés à la fois.
        feed = [(1.0, 1, "bid", "H", 5), (2.0, 1, "cancel", "H", 0), (3.0, 1, "ask", "H", 30)]
        p = table_profile(feed, me=0, duration=60, n_players=4)
        self.assertEqual(p["spread_min"], 20.0)  # personne n'a coté les deux côtés : valeur par défaut

    def test_cancels_appear_in_the_public_feed(self):
        from figgie.engine import Market
        m = Market([dict(S=0, C=0, H=2, D=0)] + [dict(S=0, C=0, H=0, D=0)] * 3)
        m.apply(0, ("ask", "H", 9), t=1.0)
        m.apply(0, ("cancel", "H"), t=2.0)
        self.assertEqual(m.events[-1], (2.0, 0, "cancel", "H", 0))


class TestNeighbors(unittest.TestCase):
    def test_choice_follows_the_nearest_tables(self):
        training = [
            ({"a": 0.0, "b": 0.0}, {"X": 5.0, "Y": 1.0}),
            ({"a": 0.1, "b": 0.0}, {"X": 4.0, "Y": 2.0}),
            ({"a": 10.0, "b": 10.0}, {"X": 0.0, "Y": 6.0}),
        ]
        model = Neighbors(training)
        self.assertEqual(model.best({"a": 0.05, "b": 0.0}, k=2), "X")
        self.assertEqual(model.best({"a": 9.0, "b": 9.0}, k=1), "Y")

    def test_several_rounds_average_their_recommendations(self):
        # Manche 1 ressemble aux tables où X rapporte 5 contre 1 ; manche 2, à la table où Y rapporte 6 contre 0.
        # En moyenne : X 2,5 et Y 3,5, donc Y.
        training = [
            ({"a": 0.0, "b": 0.0}, {"X": 5.0, "Y": 1.0}),
            ({"a": 0.1, "b": 0.0}, {"X": 4.0, "Y": 2.0}),
            ({"a": 10.0, "b": 10.0}, {"X": 0.0, "Y": 6.0}),
        ]
        model = Neighbors(training)
        self.assertEqual(model.best_many([{"a": 0.0, "b": 0.0}, {"a": 9.0, "b": 9.0}], k=1), "Y")

    def test_round_trip(self):
        model = Neighbors([({"a": 1.0}, {"X": 1.0}), ({"a": 2.0}, {"X": 2.0})])
        self.assertEqual(Neighbors.from_dict(model.to_dict()).training, model.training)


class AlwaysWide(AdaptiveBot):
    """Le bot adaptatif, avec un voisinage factice qui recommande toujours (12, 3)."""
    @classmethod
    def neighbors(cls):
        return Neighbors([({"quote_rate_mean": 0.0}, {"12,3": 1.0, "8,1": 0.0})])


class TestAdaptiveBot(unittest.TestCase):
    def test_starts_with_the_reference_then_follows_the_neighbors(self):
        match = play_match([AlwaysWide, RandomBot, ZOO["heuristique"], ZOO["marginal"]], seed=4, rounds=3, duration=40)
        memory = match.memories[0]
        self.assertEqual(memory["arms"], [DEFAULT_ARM, (12, 3), (12, 3)])
        self.assertEqual(len(memory["profiles"]), 3)

    def test_plays_only_actions_refused_because_the_market_moved(self):
        match = play_match([AlwaysWide, ZOO["marginal"], ZOO["heuristique"], RandomBot], seed=3, rounds=2, duration=40)
        for log in match.logs:
            changes = []
            for t, seat, action, ok, seen_at in log["actions"]:
                if ok:
                    changes.append((t, seat))
                elif seat == 0:
                    self.assertTrue(any(seen_at <= tc <= t and sc != 0 for tc, sc in changes))


class TestMultiRoundChunks(unittest.TestCase):
    def test_chunks_of_multi_round_games_give_the_same_values(self):
        # Avec un bot qui a une mémoire : elle ne doit ni fuir d'un morceau à l'autre, ni se perdre.
        whole = duplicate_match(AlwaysWide, ZOO["heuristique"], n_deals=4, rounds=2, duration=10)
        parts = duplicate_match(AlwaysWide, ZOO["heuristique"], n_deals=2, rounds=2, duration=10) + \
            duplicate_match(AlwaysWide, ZOO["heuristique"], n_deals=2, rounds=2, duration=10, first_deal=2)
        self.assertEqual(whole, parts)


if __name__ == "__main__":
    unittest.main()
