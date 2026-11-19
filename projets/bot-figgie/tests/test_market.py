"""Seam « carnet d'ordres » : coter, prendre, et ce que le moteur refuse."""
import unittest

from figgie.engine import IllegalAction, Market


def empty_hand(**cards):
    hand = {"S": 0, "C": 0, "H": 0, "D": 0}
    hand.update(cards)
    return hand


def market():
    # Joueur 0 : 3 cœurs. Joueur 1 : 2 piques. Joueurs 2 et 3 : rien. 300 $ chacun après l'ante.
    return Market([empty_hand(H=3), empty_hand(S=2), empty_hand(), empty_hand()])


class TestQuotes(unittest.TestCase):
    def test_new_bid_must_beat_best_bid(self):
        m = market()
        m.apply(2, ("bid", "H", 5))
        with self.assertRaises(IllegalAction):
            m.apply(3, ("bid", "H", 5))
        m.apply(3, ("bid", "H", 6))
        self.assertEqual(m.book["H"]["bid"], (6, 3))

    def test_new_ask_must_beat_best_ask(self):
        m = market()
        m.apply(0, ("ask", "H", 9))
        with self.assertRaises(IllegalAction):
            m.apply(0, ("ask", "H", 9))
        m.apply(0, ("ask", "H", 8))
        self.assertEqual(m.book["H"]["ask"], (8, 0))

    def test_cannot_ask_without_card(self):
        with self.assertRaises(IllegalAction):
            market().apply(2, ("ask", "H", 5))

    def test_cannot_bid_more_than_cash(self):
        with self.assertRaises(IllegalAction):
            market().apply(2, ("bid", "H", 301))

    def test_invalid_price_or_suit_is_refused(self):
        m = market()
        for bad in (("bid", "H", 0), ("bid", "H", 2.5), ("bid", "X", 3), ("fly", "H"), (), [], 42, "bid"):
            with self.assertRaises(IllegalAction):
                m.apply(2, bad)


class TestTrades(unittest.TestCase):
    def test_trade_moves_exactly_one_card_and_the_price(self):
        m = market()
        m.apply(0, ("ask", "H", 7))
        m.apply(2, ("buy", "H"))
        self.assertEqual(m.hands[0]["H"], 2)
        self.assertEqual(m.hands[2]["H"], 1)
        self.assertEqual(m.cash[0], 307)
        self.assertEqual(m.cash[2], 293)

    def test_every_quote_is_cancelled_after_a_trade(self):
        m = market()
        m.apply(2, ("bid", "S", 4))
        m.apply(1, ("ask", "S", 12))
        m.apply(0, ("ask", "H", 7))
        m.apply(3, ("bid", "D", 2))
        m.apply(2, ("buy", "H"))
        for suit, quote in m.book.items():
            self.assertEqual(quote, {"bid": None, "ask": None}, suit)

    def test_cannot_take_own_quote(self):
        m = market()
        m.apply(0, ("ask", "H", 7))
        with self.assertRaises(IllegalAction):
            m.apply(0, ("buy", "H"))

    def test_cannot_take_missing_quote(self):
        with self.assertRaises(IllegalAction):
            market().apply(2, ("buy", "H"))

    def test_crossing_bid_trades_at_resting_ask(self):
        m = market()
        m.apply(0, ("ask", "H", 7))
        trade = m.apply(2, ("bid", "H", 10))
        self.assertEqual(trade, (2, 0, "H", 7))

    def test_crossing_ask_trades_at_resting_bid(self):
        m = market()
        m.apply(2, ("bid", "H", 6))
        trade = m.apply(0, ("ask", "H", 3))
        self.assertEqual(trade, (2, 0, "H", 6))


if __name__ == "__main__":
    unittest.main()
