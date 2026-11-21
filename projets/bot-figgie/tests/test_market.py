"""Seam « carnet d'ordres » : une cotation par joueur et par couleur, priorité prix puis temps."""
import unittest

from figgie.engine import IllegalAction, Market


def empty_hand(**cards):
    hand = {"S": 0, "C": 0, "H": 0, "D": 0}
    hand.update(cards)
    return hand


def market():
    # Joueur 0 : 3 cœurs. Joueur 1 : 2 cœurs et 2 piques. Joueurs 2 et 3 : rien. 300 $ chacun après l'ante.
    return Market([empty_hand(H=3), empty_hand(H=2, S=2), empty_hand(), empty_hand()])


class TestQuotes(unittest.TestCase):
    def test_each_player_keeps_their_own_bid(self):
        m = market()
        m.apply(2, ("bid", "H", 5))
        m.apply(3, ("bid", "H", 4))  # moins bien que la meilleure, mais accepté : chacun a sa cotation
        self.assertEqual(m.best("H", "bid"), (5, 2))

    def test_new_quote_replaces_my_previous_one(self):
        m = market()
        m.apply(2, ("bid", "H", 5))
        m.apply(2, ("bid", "H", 3))
        self.assertEqual(m.best("H", "bid"), (3, 2))

    def test_cancel_removes_my_quotes_in_that_suit(self):
        m = market()
        m.apply(0, ("ask", "H", 9))
        m.apply(0, ("bid", "H", 2))
        m.apply(0, ("bid", "S", 3))
        m.apply(0, ("cancel", "H"))
        self.assertIsNone(m.best("H", "ask"))
        self.assertIsNone(m.best("H", "bid"))
        self.assertEqual(m.best("S", "bid"), (3, 0))  # les autres couleurs ne bougent pas

    def test_cannot_ask_without_card(self):
        with self.assertRaises(IllegalAction):
            market().apply(2, ("ask", "H", 5))

    def test_cannot_bid_more_than_cash(self):
        with self.assertRaises(IllegalAction):
            market().apply(2, ("bid", "H", 301))

    def test_invalid_actions_are_refused(self):
        m = market()
        for bad in (("bid", "H", 0), ("bid", "H", 2.5), ("bid", "X", 3), ("fly", "H"), (), [], 42, "bid"):
            with self.assertRaises(IllegalAction):
                m.apply(2, bad)


class TestTrades(unittest.TestCase):
    def test_buy_takes_the_cheapest_ask(self):
        m = market()
        m.apply(0, ("ask", "H", 9))
        m.apply(1, ("ask", "H", 7))
        self.assertEqual(m.apply(2, ("buy", "H", 7)), (2, 1, "H", 7))

    def test_equal_prices_first_come_first_served(self):
        m = market()
        m.apply(1, ("ask", "H", 7))
        m.apply(0, ("ask", "H", 7))
        self.assertEqual(m.apply(2, ("buy", "H", 7)), (2, 1, "H", 7))

    def test_my_own_quote_is_skipped(self):
        m = market()
        m.apply(0, ("ask", "H", 5))
        m.apply(1, ("ask", "H", 8))
        self.assertEqual(m.apply(0, ("buy", "H", 8)), (0, 1, "H", 8))

    def test_cannot_take_when_only_my_quote_is_there(self):
        m = market()
        m.apply(0, ("ask", "H", 7))
        with self.assertRaises(IllegalAction):
            m.apply(0, ("buy", "H", 7))

    def test_taking_requires_the_price_i_saw(self):
        m = market()
        m.apply(0, ("ask", "H", 7))
        with self.assertRaises(IllegalAction):
            m.apply(2, ("buy", "H"))

    def test_buy_is_refused_if_the_offer_got_worse(self):
        # J'ai vu une vente à 5 $, elle a disparu, la meilleure est maintenant à 9 $ : refusé.
        m = market()
        m.apply(1, ("ask", "H", 9))
        with self.assertRaises(IllegalAction):
            m.apply(2, ("buy", "H", 5))

    def test_sell_is_refused_if_the_bid_got_worse(self):
        m = market()
        m.apply(2, ("bid", "H", 3))
        with self.assertRaises(IllegalAction):
            m.apply(0, ("sell", "H", 17))

    def test_take_fills_at_the_better_displayed_price(self):
        m = market()
        m.apply(1, ("ask", "H", 4))
        self.assertEqual(m.apply(2, ("buy", "H", 6)), (2, 1, "H", 4))

    def test_trade_moves_exactly_one_card_and_the_price(self):
        m = market()
        m.apply(0, ("ask", "H", 7))
        m.apply(2, ("buy", "H", 7))
        self.assertEqual((m.hands[0]["H"], m.hands[2]["H"]), (2, 1))
        self.assertEqual((m.cash[0], m.cash[2]), (307, 293))

    def test_every_quote_is_cancelled_after_a_trade(self):
        m = market()
        m.apply(2, ("bid", "S", 4))
        m.apply(1, ("ask", "S", 12))
        m.apply(0, ("ask", "H", 7))
        m.apply(3, ("bid", "D", 2))
        m.apply(2, ("buy", "H", 7))
        for suit in "SCHD":
            self.assertIsNone(m.best(suit, "bid"), suit)
            self.assertIsNone(m.best(suit, "ask"), suit)

    def test_crossing_bid_trades_at_resting_ask(self):
        m = market()
        m.apply(0, ("ask", "H", 7))
        self.assertEqual(m.apply(2, ("bid", "H", 10)), (2, 0, "H", 7))

    def test_crossing_ask_trades_at_resting_bid(self):
        m = market()
        m.apply(2, ("bid", "H", 6))
        self.assertEqual(m.apply(0, ("ask", "H", 3)), (2, 0, "H", 6))



class TestSingleQuoteRule(unittest.TestCase):
    """Phase 5c, règle du site (figgie.com, d'après le code de Rasmus Suonio) : une seule offre par côté
    et par couleur. Une nouvelle offre doit battre celle qui est affichée, et elle la remplace."""

    def single(self):
        return Market([empty_hand(H=3), empty_hand(H=2, S=2), empty_hand(), empty_hand()], single_quote=True)

    def test_a_bid_that_does_not_beat_the_best_is_refused(self):
        m = self.single()
        m.apply(2, ("bid", "H", 5))
        for price in (4, 5):  # moins bien, ou au même prix : refusé
            with self.assertRaises(IllegalAction):
                m.apply(3, ("bid", "H", price))
        self.assertEqual(m.best("H", "bid"), (5, 2))

    def test_a_better_bid_replaces_the_displayed_one(self):
        m = self.single()
        m.apply(2, ("bid", "H", 5))
        m.apply(3, ("bid", "H", 6))
        self.assertEqual(m.best("H", "bid"), (6, 3))
        m.apply(3, ("cancel", "H"))
        self.assertIsNone(m.best("H", "bid"))  # l'offre battue ne revient pas

    def test_an_ask_must_be_lower_than_the_displayed_one(self):
        m = self.single()
        m.apply(0, ("ask", "H", 8))
        with self.assertRaises(IllegalAction):
            m.apply(1, ("ask", "H", 8))
        m.apply(1, ("ask", "H", 7))
        self.assertEqual(m.best("H", "ask"), (7, 1))
        self.assertEqual(m.apply(2, ("buy", "H", 7)), (2, 1, "H", 7))

    def test_without_the_option_each_player_keeps_a_quote(self):
        m = market()
        m.apply(2, ("bid", "H", 5))
        m.apply(3, ("bid", "H", 4))
        m.apply(2, ("cancel", "H"))
        self.assertEqual(m.best("H", "bid"), (4, 3))


if __name__ == "__main__":
    unittest.main()
