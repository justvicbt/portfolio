"""Seams « événements du marché », « modèle de signaux » et « modèle d'adversaire »."""
import math
import unittest

from figgie.bots import ZOO
from figgie.engine import play_round
from figgie.signals import OpponentModel, SignalModel, events_from_log


class Witness:
    """Ne joue jamais : garde une copie du fil d'événements à chaque regard."""
    looks = None

    def __init__(self):
        Witness.looks = []

    def act(self, view, rng):
        Witness.looks.append(list(view.events))
        return None


def strip(events):
    return [(p, kind, suit, price) for _t, p, kind, suit, price in events]


class TestMarketEvents(unittest.TestCase):
    def test_the_live_feed_matches_the_log(self):
        for seed in range(5):
            bots = [Witness, ZOO["heuristique"], ZOO["marginal"], ZOO["aleatoire"]]
            result = play_round(bots, seed=seed, duration=60)
            from_log = events_from_log(result.log)
            self.assertGreater(len(from_log), 5)
            for feed in Witness.looks:
                self.assertEqual(feed, from_log[:len(feed)])  # rien de perdu, dans le bon ordre
            self.assertEqual(result.events, from_log)

    def test_a_trade_gives_one_event_on_each_side(self):
        log = {"format": 2, "hands": [dict(S=0, C=0, H=2, D=0), dict(S=0, C=0, H=0, D=0),
                                      dict(S=0, C=0, H=0, D=0), dict(S=0, C=0, H=0, D=0)],
               "goal": "H", "actions": [[1.0, 0, ["ask", "H", 7], True, 0.9],
                                        [2.0, 1, ["buy", "H", 7], True, 1.9],
                                        [3.0, 2, ["sell", "H", 3], False, 2.9]]}
        self.assertEqual(strip(events_from_log(log)),
                         [(0, "ask", "H", 7), (1, "bought", "H", 7), (0, "sold", "H", 7)])


# Deux manches écrites à la main.
# Manche 1, objectif cœur : le joueur 1 propose 12 $ pour un cœur, le joueur 2 vend un pique à 2 $.
# Manche 2, objectif pique : le joueur 1 propose 12 $ pour un pique, le joueur 3 vend un trèfle à 2 $.
ROUNDS = [
    ([(0, 1, "bid", "H", 12), (0, 2, "ask", "S", 2)], "H"),
    ([(0, 1, "bid", "S", 12), (0, 3, "ask", "C", 2)], "S"),
]
# Fréquences par manche et par couleur, lissées de 0,5 : la couleur objectif et sa jumelle sont
# observées 2 fois (une par manche), les deux autres couleurs 4 fois.
# Offre à 12 $ : objectif (2 + 0,5) / 2 = 1,25 ; jumelle 0,5 / 2 = 0,25 ; autre 0,5 / 4 = 0,125.
# Vente à 2 $ : objectif 0,5 / 2 = 0,25 ; jumelle (1 + 0,5) / 2 = 0,75 ; autre (1 + 0,5) / 4 = 0,375.


class TestSignalModel(unittest.TestCase):
    def setUp(self):
        self.model = SignalModel.fit(ROUNDS)

    def test_learned_ratios_match_the_hand_computation(self):
        goal, twin = self.model.log_ratios("bid", 12)
        self.assertAlmostEqual(goal, math.log(10))   # 1,25 / 0,125
        self.assertAlmostEqual(twin, math.log(2))    # 0,25 / 0,125
        goal, twin = self.model.log_ratios("ask", 2)
        self.assertAlmostEqual(goal, math.log(2 / 3))
        self.assertAlmostEqual(twin, math.log(2))

    def test_one_high_bid_in_hearts_raises_hearts(self):
        # Cœur objectif : rapport 10. Carreau objectif : le cœur serait sa jumelle, rapport 2. Pique et trèfle : 1.
        uniform = dict.fromkeys("SCHD", 0.25)
        post = self.model.posterior(uniform, [(0, 1, "bid", "H", 12)])
        self.assertAlmostEqual(post["H"], 10 / 14)
        self.assertAlmostEqual(post["D"], 2 / 14)
        self.assertAlmostEqual(post["S"], 1 / 14)

    def test_my_own_events_and_ignored_players_change_nothing(self):
        uniform = dict.fromkeys("SCHD", 0.25)
        events = [(0, 1, "bid", "H", 12)]
        self.assertEqual(self.model.posterior(uniform, events, me=1), uniform)
        self.assertEqual(self.model.posterior(uniform, events, player_weights={1: 0.0}), uniform)

    def test_a_repeated_quote_counts_once(self):
        # Reposter la même offre ne dit rien de plus : une seule preuve, pas trois.
        uniform = dict.fromkeys("SCHD", 0.25)
        once = self.model.posterior(uniform, [(0, 1, "bid", "H", 12)])
        thrice = self.model.posterior(uniform, [(0, 1, "bid", "H", 12), (1, 1, "bid", "H", 13), (2, 1, "bid", "H", 12)])
        self.assertEqual(once, thrice)  # 12 et 13 $ tombent dans la même tranche de prix

    def test_a_quotes_only_model_ignores_trades(self):
        # Les échanges sont déjà comptés par le comptage des cartes : ce modèle-là ne les relit pas.
        model = SignalModel.fit(ROUNDS + [([(0, 1, "bought", "H", 9)], "H")], kinds=("bid", "ask"))
        uniform = dict.fromkeys("SCHD", 0.25)
        self.assertEqual(model.posterior(uniform, [(0, 1, "bought", "H", 9)]), uniform)
        again = SignalModel.from_dict(model.to_dict())
        self.assertEqual(again.kinds, ("bid", "ask"))

    def test_temper_shrinks_the_evidence(self):
        uniform = dict.fromkeys("SCHD", 0.25)
        post = self.model.posterior(uniform, [(0, 1, "bid", "H", 12)], temper=0.5)
        self.assertAlmostEqual(post["H"], 10 ** 0.5 / (10 ** 0.5 + 2 ** 0.5 + 2))

    def test_model_survives_a_json_round_trip(self):
        import json
        again = SignalModel.from_dict(json.loads(json.dumps(self.model.to_dict())))
        self.assertEqual(again.log_ratios("bid", 12), self.model.log_ratios("bid", 12))


def synthetic_rounds(n, rng):
    """Le joueur 1 propose 12 $ dans la couleur objectif ; le joueur 2 propose 12 $ dans une couleur au hasard."""
    rounds = []
    for _ in range(n):
        goal = rng.choice("SCHD")
        events = [(0, 1, "bid", goal, 12)] * 3 + [(0, 2, "bid", rng.choice("SCHD"), 12) for _ in range(3)]
        rounds.append((events, goal))
    return rounds


class TestOpponentModel(unittest.TestCase):
    def test_reliable_player_gains_weight_and_random_player_loses_it(self):
        import random
        rng = random.Random(0)
        model = SignalModel.fit(synthetic_rounds(500, rng))
        opponents = OpponentModel(model)
        self.assertEqual(opponents.weight(1), 1.0)  # avant de l'avoir vu jouer, confiance par défaut
        for events, goal in synthetic_rounds(20, rng):
            opponents.observe_round(events, goal, me=0)
        self.assertGreater(opponents.weight(1), 1.2)
        self.assertLess(opponents.weight(2), 0.3)

    def test_my_own_events_are_not_judged(self):
        opponents = OpponentModel(SignalModel.fit(ROUNDS))
        opponents.observe_round([(0, 1, "bid", "H", 12)], "H", me=1)
        self.assertEqual(opponents.weight(1), 1.0)


if __name__ == "__main__":
    unittest.main()
