"""Seam « journal de partie » : le journal suffit à reconstruire la manche."""
import json
import unittest

from figgie.engine import play_round, replay
from figgie.bots import RandomBot


class TestLog(unittest.TestCase):
    def test_replaying_the_json_log_gives_the_same_profits(self):
        for seed in range(20):
            result = play_round([RandomBot] * 4, seed=seed, duration=40)
            log = json.loads(json.dumps(result.log))
            self.assertEqual(replay(log), result.profits)

    def test_log_records_the_trades(self):
        result = play_round([RandomBot] * 5, seed=3, duration=40)
        self.assertGreater(sum(a[3] for a in result.log["actions"]), 0)

    def test_log_from_an_older_version_is_refused_clearly(self):
        log = json.loads(json.dumps(play_round([RandomBot] * 4, seed=1, duration=10).log))
        del log["format"]
        with self.assertRaisesRegex(ValueError, "format"):
            replay(log)

    def test_tampered_log_is_detected(self):
        result = play_round([RandomBot] * 4, seed=1, duration=40)
        log = json.loads(json.dumps(result.log))
        accepted = next(a for a in log["actions"] if a[3])
        accepted[3] = False  # on prétend qu'une action acceptée a été refusée
        with self.assertRaises(ValueError):
            replay(log)


if __name__ == "__main__":
    unittest.main()
