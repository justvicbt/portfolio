"""Phase 5c, seam « statistiques du marché » : les mêmes mesures sur les vraies manches de figgie.com
(journaux de Rasmus Suonio) et sur nos manches simulées."""
import unittest

from figgie.reel import ask_outcomes, lift_rates, market_stats, parse_rasmus_round

# Une manche écrite à la main, au format des journaux de Rasmus : genre, secondes restantes, couleur
# (0 = pique, 1 = trèfle, 2 = cœur, 3 = carreau), prix, joueur (acheteur>vendeur pour un échange).
# Son bot est au siège 0, les bots Hard aux sièges 1 à 3.
ROUND = {"goal": "hearts", "me": 0, "log": ";".join([
    "b,236,2,3,1,,",       # t = 4 s : le siège 1 propose 3 $ pour un cœur
    "o,235,2,9,2,,",       # t = 5 s : le siège 2 vend un cœur à 9 $
    "b,230,2,4,3,,",       # t = 10 s : le siège 3 propose 4 $
    "t,200,2,9,3>2,0.5/0.5/0/0,F",  # t = 40 s : le siège 3 achète le cœur du siège 2 à 9 $
    "o,190,0,2,1,,",       # t = 50 s : le siège 1 vend un pique à 2 $
    "xo,185,0,2,1,,",      # t = 55 s : et le retire
    "t,30,0,2,2>1,,",      # t = 210 s : le siège 2 achète un pique au siège 1 à 2 $
    "t,20,0,3,0>3,,",      # t = 220 s : le bot de Rasmus achète un pique au siège 3 (pas entre bots Hard)
])}


class TestRealLogs(unittest.TestCase):
    def test_a_real_round_becomes_our_public_feed(self):
        r = parse_rasmus_round(ROUND)
        self.assertEqual(r["goal"], "H")
        self.assertEqual(r["hard"], [1, 2, 3])
        self.assertEqual(r["events"][:4], [(4, 1, "bid", "H", 3), (5, 2, "ask", "H", 9), (10, 3, "bid", "H", 4),
                                           (40, 3, "bought", "H", 9)])
        self.assertEqual(r["events"][4:7], [(40, 2, "sold", "H", 9), (50, 1, "ask", "S", 2), (55, 1, "cancel", "S", 0)])
        self.assertEqual(len(r["events"]), 11)

    def test_market_statistics_of_a_hand_written_round(self):
        stats = market_stats([parse_rasmus_round(ROUND)])
        self.assertEqual(stats["trades"], 3)
        self.assertAlmostEqual(stats["hard_trades_per_pair"], 2 / 3)  # 2 échanges entre bots Hard, 3 paires
        self.assertEqual(stats["by_minute"], [0.5, 0.0, 0.0, 0.5])
        self.assertEqual(stats["quotes_per_min"], 0.25)  # médiane : 2, 1 et 1 cotations en 4 minutes
        self.assertEqual(stats["first_quote"], 5)
        self.assertEqual(stats["goal_price"], 9)
        self.assertEqual(stats["other_price"], 2)
        self.assertEqual(stats["goal_top_bid"], 3)  # plus haut prix proposé pour un cœur : 3, 0 et 4
        self.assertEqual(stats["other_top_bid"], 0)


# Phase 5j : ce que deviennent les offres de vente. Cœur = objectif ; le bot de Rasmus au siège 0.
ASKS = {"goal": "hearts", "me": 0, "log": ";".join([
    "o,236,2,9,1,,",       # t = 4 s : le siège 1 vend un cœur à 9 $
    "o,235,2,8,2,,",       # t = 5 s : le siège 2 le bat à 8 $ : l'offre à 9 $ est remplacée
    "t,230,2,8,3>2,,",     # t = 10 s : le siège 3 prend l'offre à 8 $
    "o,220,0,5,1,,",       # t = 20 s : le siège 1 vend un pique à 5 $
    "xo,215,0,5,1,,",      # t = 25 s : et la retire
    "o,210,1,6,3,,",       # t = 30 s : le siège 3 vend un trèfle à 6 $
    "b,205,1,4,2,,",       # t = 35 s : le siège 2 propose 4 $ pour un trèfle
    "t,200,1,4,2>1,,",     # t = 40 s : le siège 1 lui vend un trèfle : l'échange efface l'offre à 6 $
    "o,100,3,12,0,,",      # t = 140 s : le bot de Rasmus vend un carreau à 12 $, jamais pris
])}


class TestAskOutcomes(unittest.TestCase):
    def test_each_ask_ends_taken_replaced_cancelled_cleared_or_still_there(self):
        self.assertEqual(ask_outcomes(parse_rasmus_round(ASKS)), [
            ("hard", True, 9, "remplacée", None),
            ("hard", True, 8, "prise", "hard"),
            ("hard", False, 5, "retirée", None),
            ("hard", False, 6, "effacée", None),
            ("autre", False, 12, "fin", None),
        ])

    def test_a_trade_clears_the_asks_of_every_suit_and_a_bid_cancel_keeps_the_ask(self):
        cross = {"goal": "hearts", "me": 0, "log": ";".join([
            "o,236,0,7,1,,",       # t = 4 s : le siège 1 vend un pique à 7 $
            "b,235,1,4,2,,",       # t = 5 s : le siège 2 propose 4 $ pour un trèfle
            "t,230,1,4,2>3,,",     # t = 10 s : le siège 3 lui vend un trèfle : tout le carnet est vidé
            "b,225,0,7,2,,",       # t = 15 s : le siège 2 propose 7 $ pour un pique
            "t,220,0,7,2>1,,",     # t = 20 s : le siège 1 lui vend : c'est une offre d'achat prise, pas la sienne
            "o,210,2,8,3,,",       # t = 30 s : le siège 3 vend un cœur à 8 $
            "b,205,2,3,3,,",       # t = 35 s : et propose 3 $ pour un cœur
            "xb,200,2,0,3,,",      # t = 40 s : il retire son offre d'achat ; son offre de vente reste
            "t,190,2,8,1>3,,",     # t = 50 s : le siège 1 prend l'offre à 8 $
        ])}
        self.assertEqual(ask_outcomes(parse_rasmus_round(cross)), [
            ("hard", False, 7, "effacée", None),
            ("hard", True, 8, "prise", "hard"),
        ])

    def test_share_of_the_hard_asks_that_a_hard_bot_takes(self):
        rates = lift_rates([parse_rasmus_round(ASKS)])
        self.assertEqual(rates["objectif 7-10"], 0.5)  # une offre à 8 $ prise, une à 9 $ remplacée
        self.assertEqual(rates["autre 4-6"], 0.0)      # retirée et effacée ; l'offre du bot de Rasmus ne compte pas
        self.assertIsNone(rates["autre 1-3"])          # aucune offre dans cette tranche


def close_to_the_site(stats, real):
    """Une table simulée ressemble au site : chaque mesure entre 0,6 et 1,5 fois celle des journaux,
    et des échanges de plus en plus nombreux au fil de la manche."""
    keys = ["hard_trades_per_pair", "quotes_per_min", "goal_price", "other_price", "goal_top_bid", "other_top_bid"]
    off = {k: (stats[k], real[k]) for k in keys if not stats[k] or not 0.6 <= stats[k] / real[k] <= 1.5}
    quarters = stats["by_minute"]
    if not all(a < b for a, b in zip(quarters, quarters[1:])):
        off["by_minute"] = (quarters, real["by_minute"])
    return off


class TestSimulatedHardBot(unittest.TestCase):
    """Le Hard simulé, réglé sur les journaux (figgie.calibrate), joué avec la règle du site."""

    def test_a_table_of_simulated_hard_bots_looks_like_the_site(self):
        from figgie.bots import HardBot
        from figgie.engine import play_round
        from figgie.reel import load_rasmus, simulated_round
        real = market_stats(load_rasmus())
        def table(bot):
            return market_stats([simulated_round(play_round([bot] * 4, seed=33_000_000 + g, single_quote=True))
                                 for g in range(30)])
        self.assertEqual(close_to_the_site(table(HardBot), real), {})
        from figgie.bots import ZOO
        self.assertNotEqual(close_to_the_site(table(ZOO["marginal"]), real), {})  # le test sait dire non



class CheapHeartBuyer:
    """Bot de test : achète tout cœur proposé à 5 $ ou moins, et cote un pique à 2 $ (jamais servi)."""
    def act(self, view, rng):
        ask = view.best("H", "ask")
        if ask and ask[0] <= 5:
            return ("buy", "H", ask[0])
        if view.mine("S", "bid") is None:
            return ("bid", "S", 2)
        return None


PAPER_ROUND = {"goal": "hearts", "me": 0, "dealt": [2, 2, 3, 3], "log": ";".join([
    "b,239,0,1,0,,",      # t = 1 s : le bot de Rasmus cote (il est remplacé par le nôtre : ignoré)
    "o,236,2,6,1,,",      # t = 4 s : le siège 1 vend un cœur à 6 $ (trop cher)
    "o,230,2,5,2,,",      # t = 10 s : le siège 2 le vend à 5 $ : on le prend
    "b,225,0,8,3,,",      # t = 15 s : rien à prendre en cœur, la vente à 5 $ a disparu
    "t,200,1,4,1>2,,",    # t = 40 s : un échange entre deux autres vide le carnet
    "o,190,2,3,3,,",      # t = 50 s : le siège 3 vend un cœur à 3 $ : on le prend
    "t,100,3,6,0>1,,",    # t = 140 s : le bot de Rasmus achète vraiment un carreau (ça a eu lieu)
])}


class TestPaperReplay(unittest.TestCase):
    """Phase 5c, seam « rejeu des vraies manches » : notre bot à la place de celui de Rasmus, qui peut
    prendre les vraies cotations des bots du site sans changer le marché."""

    def test_our_bot_takes_the_real_quotes_it_wants(self):
        from figgie.reel import paper_replay
        score, takes = paper_replay(parse_rasmus_round(PAPER_ROUND), CheapHeartBuyer)
        self.assertEqual(takes, [(10, 0, 2, "H", 5), (50, 0, 3, "H", 3)])  # (instant, acheteur, vendeur, couleur, prix)
        self.assertEqual(score, -8 + 2 * 10)  # 8 $ payés, deux cartes objectif de plus à la cloche

    def test_a_real_sale_of_a_card_already_sold_on_paper_is_struck(self):
        from figgie.reel import paper_replay

        class HeartSeller:
            def act(self, view, rng):
                bid = view.best("H", "bid")
                return ("sell", "H", bid[0]) if bid and bid[0] >= 4 and view.hand["H"] > 0 else None
        rnd = {"goal": "hearts", "me": 0, "dealt": [3, 3, 2, 2], "log": ";".join([
            "b,230,2,5,1,,",     # on vend un cœur au siège 1 à 5 $
            "b,220,2,4,2,,",     # puis notre dernier cœur au siège 2 à 4 $
            "t,200,2,6,3>0,,",   # le bot de Rasmus vend vraiment un cœur à 6 $ : impossible sur le papier
        ])}
        score, takes = paper_replay(parse_rasmus_round(rnd), HeartSeller)
        self.assertEqual(len(takes), 2)
        # +9 $ de prises, -6 $ de la vente rayée ; à la cloche 0 cœur, contre 1 pour le vrai bot de Rasmus
        self.assertEqual(score, 9 - 6 - 10)


class TestPaperMajority(unittest.TestCase):
    """Phase 5e, seam « majorité estimée » : les mains des bots du site sont tirées parmi celles qui
    expliquent le journal et le vrai gain de Rasmus, puis la majorité est rejouée avec nos prises."""

    def test_buying_the_majority_on_paper_counts_the_pot(self):
        from figgie.reel import paper_replay
        # Rasmus garde ses 5 cœurs et partage la majorité : 10 $ x 5 + 50 $ de part, moins 50 $ de mise.
        rnd = {"goal": "hearts", "me": 0, "dealt": [0, 0, 5, 5], "final": [0, 0, 5, 5], "pnl": 50,
               "log": ";".join(f"o,{230 - 10 * i},2,2,1,," for i in range(4))}  # le siège 1 vend 4 cœurs à 2 $
        r = parse_rasmus_round(rnd)
        self.assertEqual(r["majority"], 50)
        score, takes = paper_replay(r, CheapHeartBuyer, majority=True)
        self.assertEqual(len(takes), 4)
        # 9 cœurs : le paquet en a 10 et le siège 1 n'en a plus qu'un. La majorité seule vaut 100 $.
        self.assertAlmostEqual(score, -8 + 4 * 10 + (100 - 50))
        self.assertEqual(paper_replay(r, CheapHeartBuyer)[0], -8 + 4 * 10)  # sans la majorité, comme avant


class TestSiteReading(unittest.TestCase):
    """Phase 5d, seam « lecture du marché sur les vraies manches » : le modèle de signaux appris sur des
    tables simulées du site (figgie.learn --site), avec la confiance apprise d'une manche à l'autre.
    À une minute, il ne doit pas faire nettement pire que la donne seule (écarts par manche, IC à 95 %) ;
    à la cloche, il doit trouver la bonne couleur dans au moins 85 % des manches."""

    def test_no_worse_than_the_hand_after_one_minute_and_finds_the_goal_at_the_bell(self):
        from figgie.evaluate import mean_ci
        from figgie.reel import goal_calibration, load_rasmus
        cal = goal_calibration(load_rasmus(), times=(60, 239), per_round=True)

        def not_worse_than_the_hand(method):
            return all(mean_ci([a[i] - b[i] for a, b in zip(cal[method][60], cal["donne"][60])])[2] >= 0
                       for i in (0, 1))  # P de la vraie couleur, et bonne couleur ou non
        self.assertTrue(not_worse_than_the_hand("lecture site"))
        at_bell = cal["lecture site"][239]
        self.assertGreaterEqual(sum(x[1] for x in at_bell) / len(at_bell), 0.85)
        self.assertFalse(not_worse_than_the_hand("lecture"))  # le test sait dire non : la lecture de la phase 3


if __name__ == "__main__":
    unittest.main()
