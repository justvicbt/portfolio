"""Seam « comportements anormaux » : joueur inactif, spam de cotations, faux signaux."""
import math
import unittest

from figgie.bots import ABNORMAL, ZOO
from figgie.engine import MIN_DELAY, play_round


class TestAbnormalPlayers(unittest.TestCase):
    def test_idle_player_never_acts_and_the_round_still_works(self):
        result = play_round([ABNORMAL["inactif"], ZOO["marginal"], ZOO["heuristique"], ZOO["aleatoire"]], seed=1)
        self.assertEqual([a for a in result.log["actions"] if a[1] == 0], [])
        self.assertTrue(math.isclose(sum(result.profits), 0, abs_tol=1e-9))

    def test_spam_is_capped_by_the_engine(self):
        duration = 30
        result = play_round([ABNORMAL["spammeur"], ZOO["marginal"], ZOO["heuristique"], ZOO["sniper"]],
                            seed=2, duration=duration)
        spam = [a for a in result.log["actions"] if a[1] == 0]
        self.assertGreater(len(spam), 100)                    # il spamme vraiment
        self.assertLessEqual(len(spam), duration / MIN_DELAY + 1)  # mais pas plus vite que la limite
        self.assertTrue(math.isclose(sum(result.profits), 0, abs_tol=1e-9))

    def test_liar_posts_fake_bids_and_withdraws_them(self):
        result = play_round([ABNORMAL["menteur"], ZOO["lecteur"], ZOO["heuristique"], ZOO["marginal"]], seed=3)
        mine = [a for a in result.log["actions"] if a[1] == 0 and a[3]]
        fakes = [a for a in mine if a[2][0] == "bid" and a[2][2] == ABNORMAL["menteur"].fake_price]
        cancels = [a for a in mine if a[2][0] == "cancel"]
        self.assertGreater(len(fakes), 0)
        self.assertGreater(len(cancels), 0)
        self.assertTrue(math.isclose(sum(result.profits), 0, abs_tol=1e-9))


class TestLiarKeepsItsRealQuotes(unittest.TestCase):
    def test_fake_bids_are_never_refused_and_real_offers_come_back(self):
        # La fausse offre ne doit jamais croiser une vente, même la sienne (elle serait refusée).
        # Son retrait annule aussi la vraie vente du menteur dans cette couleur : il doit la reposter ensuite.
        from figgie.engine import Market
        liar = ABNORMAL["menteur"]
        for seed in range(4):
            result = play_round([liar, ZOO["lecteur"], ZOO["heuristique"], ZOO["marginal"]], seed=seed)
            market = Market(result.log["hands"])
            for t, seat, action, ok, _ in result.log["actions"]:
                if seat == 0 and action[0] == "bid" and action[2] == liar.fake_price:
                    self.assertTrue(ok, (seed, t))  # jamais refusée pour avoir croisé sa propre vente
                if ok:
                    market.apply(seat, action, t)
            asks = [a for a in result.log["actions"] if a[1] == 0 and a[3] and a[2][0] == "ask"]
            cancels = [a for a in result.log["actions"] if a[1] == 0 and a[3] and a[2][0] == "cancel"]
            if cancels:  # après un mensonge, il recote encore des ventes
                self.assertTrue(any(a[0] > cancels[0][0] for a in asks), seed)


if __name__ == "__main__":
    unittest.main()
