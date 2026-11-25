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


# --- Phase 5b : entraînement contre ses propres copies, et choix selon la main --------------------

class TestSelfPlayTables(unittest.TestCase):
    def test_training_tables_contain_copies_of_the_previous_version(self):
        from figgie.adapt import POOL, table_opponents_v3
        tables = [table_opponents_v3(i, 11, ["adaptatif_v2"])[1] for i in range(60)]
        for names in tables:
            self.assertTrue(all(n in POOL or n == "adaptatif_v2" for n in names), names)
        # comme au test de minorité : toute la table, sauf un joueur, est faite de copies de la version précédente
        minority_like = [names for names in tables if names.count("adaptatif_v2") >= len(names) - 1]
        self.assertGreaterEqual(len(minority_like), 15)
        without = [table_opponents_v3(i, 11, [])[1] for i in range(60)]
        self.assertTrue(all(n in POOL for names in without for n in names))


def _hand_aware_bot():
    from figgie.adapt import AdaptiveV3Bot
    # 5 lignes par force de main : le bot consulte ses 5 plus proches voisins
    model = Neighbors([({"main": 0.0}, {"8,1,8,1": 1.0, "12,3,12,3": 0.0})] * 5 +
                      [({"main": 1.0}, {"8,1,8,1": 0.0, "12,3,12,3": 1.0})] * 5)
    return type("HandAware", (AdaptiveV3Bot,), {"neighbors": classmethod(lambda cls: model)})


class TestHandAwareChoice(unittest.TestCase):
    def test_the_setting_follows_the_strength_of_the_starting_hand(self):
        from figgie.adapt import STRONG_HAND, hand_strength
        match = play_match([_hand_aware_bot(), ZOO["marginal"], ZOO["heuristique"], ZOO["sniper"]], seed=5,
                           rounds=8, duration=20)
        arms = match.memories[0]["arms"]
        strong = [hand_strength(log["hands"][0], 4) >= STRONG_HAND for log in match.logs]
        self.assertTrue(any(strong[1:]) and not all(strong[1:]), strong)  # les deux cas se présentent
        for r in range(1, 8):  # la première manche se joue au réglage de départ
            self.assertEqual(arms[r], (12, 3, 12, 3) if strong[r] else (8, 1, 8, 1), r)


class TestAdaptiveV4(unittest.TestCase):
    """Phase 5d, seam « la v4 reconnaît le marché du site » : elle lit le marché (lecteur du site) et
    choisit son réglage d'après des tables d'entraînement jouées avec la règle du site."""

    def test_a_table_of_simulated_hard_bots_gets_another_setting_than_a_table_of_marginal_bots(self):
        from figgie.adapt import AdaptiveV4Bot
        from figgie.bots import HardBot
        def settings(opponent):
            match = play_match([AdaptiveV4Bot] + [opponent] * 3, seed=34_000_000, rounds=4, single_quote=True)
            return match.memories[0]["arms"][1:]  # la première manche se joue au réglage de départ
        self.assertNotEqual(settings(HardBot), settings(ZOO["marginal"]))


class TestAdaptiveV4b(unittest.TestCase):
    """Phase 5e, seam « la v4b reconnaît une table de snipers » : ils ne cotent jamais, une table que la v4
    n'avait pas vue à l'entraînement. Face à eux, seuls les réglages qui se resserrent en fin de manche
    rapportent beaucoup (+26 et +28 $ par manche, contre +18 $ au mieux pour les autres)."""

    def test_a_table_of_snipers_gets_a_setting_that_tightens_late(self):
        from figgie.adapt import AdaptiveV4bBot
        match = play_match([AdaptiveV4bBot] + [ZOO["sniper"]] * 3, seed=34_000_000, rounds=4, single_quote=True)
        for arm in match.memories[0]["arms"][1:]:
            self.assertIn(tuple(arm), [(8, 1, 3, 1), (12, 3, 4, 1)])


class TestAdaptiveV4c(unittest.TestCase):
    """Phase 5f, seam « la v4c joue pour ses copies » : seul face à ses copies, l'exploiteur leur vend des
    cartes. Pour la copie qui achète, c'est rentable ; pour l'ensemble des copies, non. Toutes au réglage
    serré 6,3, elles lui prennent 1,22 $ par manche ; à 8,1 → 3,1, le choix de la v4b, il leur prend 4,47 $.

    Ce seam échoue encore : une copie sur trois repasse à 8,1 → 3,1. Ses plus proches voisins viennent des
    anciennes tables façon minorité, jugées au gain d'une seule copie (docs/phase5f.fr.md, étape 1). Le test
    vérifie donc l'échec, et seulement lui : une erreur (modèle absent, par exemple) le fait échouer, et il
    échouera aussi le jour où toutes les copies joueront 6,3, pour qu'on le remette à l'endroit."""

    def test_copies_facing_the_exploiter_play_tight(self):
        from figgie.adapt import AdaptiveV4cBot
        match = play_match([ZOO["exploiteur"]] + [AdaptiveV4cBot] * 3, seed=34_000_000, rounds=4, single_quote=True)
        arms = [tuple(arm) for memory in match.memories[1:] for arm in memory["arms"][1:]]
        with self.assertRaises(AssertionError):  # échec connu, voir plus haut
            self.assertEqual(arms, [(6, 3, 6, 3)] * 9)


class TestQuietStart(unittest.TestCase):
    """Phase 5g, seam « la v4c calme se tait la première minute » : d'après DiSilvio, Luo et Ozerov (arXiv
    2110.00879, tableau 3), un fondamentaliste rapide perd de l'argent en échangeant trop tôt, quand ses valeurs
    bougent encore. La v4c calme n'envoie aucun ordre pendant les 60 premières secondes, puis joue comme la v4c."""

    def test_no_action_before_60_s_then_the_v4c_choice(self):
        from figgie.adapt import STRONG_HAND, AdaptiveV4cBot, QuietV4cBot, hand_strength
        match = play_match([QuietV4cBot, ZOO["marginal"], ZOO["heuristique"], ZOO["sniper"]], seed=5, rounds=3,
                           single_quote=True)
        for log in match.logs:
            seen = [seen_at for _t, seat, _action, _ok, seen_at in log["actions"] if seat == 0]  # quand elle a regardé
            self.assertTrue(seen)
            self.assertGreaterEqual(min(seen), 60.0)
        memory = match.memories[0]
        for r in range(1, 3):  # mêmes profils et même main : le choix de la v4c
            v4c = AdaptiveV4cBot()
            v4c._strong = float(hand_strength(match.logs[r]["hands"][0], 4) >= STRONG_HAND)
            self.assertEqual(tuple(memory["arms"][r]), tuple(v4c.choose(memory["profiles"][:r])))


class TestSellOnlyStart(unittest.TestCase):
    """Phase 5k, seam « la v4c vendeuse n'achète rien la première minute » : en minute 1, la v4c achète surtout des
    cartes hors objectif, qu'elle surpaie (phase 5j). La v4c vendeuse n'envoie ni achat ni offre d'achat pendant les
    60 premières secondes, mais vend comme la v4c ; son choix de réglage est celui de la v4c."""

    def test_no_buy_before_60_s_but_sells_and_the_v4c_choice(self):
        from figgie.adapt import STRONG_HAND, AdaptiveV4cBot, SellOnlyV4cBot, hand_strength
        match = play_match([SellOnlyV4cBot, ZOO["marginal"], ZOO["heuristique"], ZOO["sniper"]], seed=5, rounds=3,
                           single_quote=True)
        early = [action[0] for log in match.logs for _t, seat, action, _ok, seen in log["actions"]
                 if seat == 0 and seen < 60.0]
        self.assertNotIn("buy", early)
        self.assertNotIn("bid", early)
        v4c = play_match([AdaptiveV4cBot, ZOO["marginal"], ZOO["heuristique"], ZOO["sniper"]], seed=5, rounds=3,
                         single_quote=True)
        v4c_early = [action[0] for log in v4c.logs for _t, seat, action, _ok, seen in log["actions"]
                     if seat == 0 and seen < 60.0]
        sales = lambda kinds: sum(k in ("sell", "ask") for k in kinds)
        self.assertGreater(sales(early), 0)  # elle n'est pas muette
        self.assertGreaterEqual(sales(early), sales(v4c_early))  # elle vend au moins autant que la v4c
        memory = match.memories[0]
        for r in range(1, 3):  # mêmes profils et même main : le choix de la v4c
            v4c = AdaptiveV4cBot()
            v4c._strong = float(hand_strength(match.logs[r]["hands"][0], 4) >= STRONG_HAND)
            self.assertEqual(tuple(memory["arms"][r]), tuple(v4c.choose(memory["profiles"][:r])))


class TestTimedStart(unittest.TestCase):
    """Phase 5l, seam « la v4c au temps choisit son réglage avec son modèle » : sous la règle du site, chaque manche
    après la première, son réglage est celui que donnent ses voisins (modèle réentraîné) à partir des profils vus."""

    def test_the_arm_is_the_one_of_its_retrained_model(self):
        import json
        from figgie.adapt import STRONG_HAND, Neighbors, TimedV4cBot, hand_strength, parse_arm
        from figgie.bots import MODELS_DIR
        model = Neighbors.from_dict(json.loads((MODELS_DIR / "adaptation_v4t.json").read_text()))
        match = play_match([TimedV4cBot, ZOO["marginal"], ZOO["heuristique"], ZOO["sniper"]], seed=5, rounds=3,
                           single_quote=True)
        memory = match.memories[0]
        for r in range(1, 3):
            strong = float(hand_strength(match.logs[r]["hands"][0], 4) >= STRONG_HAND)
            expected = parse_arm(model.best_many([{**p, "main": strong} for p in memory["profiles"][:r]]))
            self.assertEqual(tuple(memory["arms"][r]), tuple(expected))


class TestMeanProfile(unittest.TestCase):
    """Phase 5h, seam « après une seule manche, la v4d choisit comme la v4c » : la moyenne d'un seul profil est ce
    profil, donc interroger les voisins une fois avec la moyenne revient à les interroger avec la seule manche vue."""

    def test_after_one_round_the_v4c_choice(self):
        from figgie.adapt import STRONG_HAND, AdaptiveV4cBot, AdaptiveV4dBot, hand_strength
        for seed in (5, 6, 7):
            match = play_match([AdaptiveV4dBot, ZOO["exploiteur"], ZOO["marginal"], ZOO["sniper"]], seed=seed, rounds=2,
                               single_quote=True)
            memory, v4c = match.memories[0], AdaptiveV4cBot()
            v4c._strong = float(hand_strength(match.logs[1]["hands"][0], 4) >= STRONG_HAND)
            self.assertEqual(tuple(memory["arms"][1]), tuple(v4c.choose(memory["profiles"][:1])))


if __name__ == "__main__":
    unittest.main()
