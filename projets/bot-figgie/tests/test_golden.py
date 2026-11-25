"""Seam « moteur accéléré » : des manches fixées donnent exactement les mêmes résultats qu'avant.

Les valeurs de référence (fixtures/golden.json) ont été enregistrées avec le moteur de la phase 3,
avant toute accélération. Si ce test échoue, une optimisation a changé le comportement du jeu.
Régénérées en phase 5m, après la correction de la valeur d'achat du marginal (mêmes tables, mêmes graines) :
seule la table sans bot à valeur marginale est restée identique.
"""
import hashlib
import json
import unittest
from pathlib import Path

from figgie.bots import ZOO
from figgie.engine import play_match, play_round

GOLDEN = json.loads((Path(__file__).parent / "fixtures" / "golden.json").read_text())


def digest(obj):
    return hashlib.sha256(json.dumps(obj, sort_keys=True).encode()).hexdigest()


class TestGolden(unittest.TestCase):
    def setUp(self):
        # Les tables avec un lecteur dépendent du modèle appris : s'il a changé, ce n'est pas le moteur.
        model = (Path(__file__).parent.parent / "modeles" / "signaux.json").read_bytes()
        self.assertEqual(hashlib.sha256(model).hexdigest(), GOLDEN["model_sha256"],
                         "modeles/signaux.json a changé (figgie.learn relancé ?) : régénérer fixtures/golden.json")

    def test_rounds_are_unchanged(self):
        for case in GOLDEN["rounds"]:
            result = play_round([ZOO[n] for n in case["bots"]], seed=case["seed"])
            self.assertEqual(result.profits, case["profits"], case["bots"])
            self.assertEqual(digest(result.log), case["log_sha256"], case["bots"])

    def test_match_is_unchanged(self):
        match = play_match([ZOO[n] for n in ["lecteur", "aleatoire", "heuristique", "marginal"]], seed=5, rounds=3)
        self.assertEqual(match.profits, GOLDEN["match"]["profits"])
        self.assertEqual(digest(match.logs), GOLDEN["match"]["log_sha256"])


if __name__ == "__main__":
    unittest.main()
