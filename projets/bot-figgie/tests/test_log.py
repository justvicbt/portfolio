"""Seam « journal de partie » : le journal suffit à reconstruire la manche."""
import json
import unittest

from figgie.engine import play_round, replay
from figgie.bots import RandomBot


class TestLog(unittest.TestCase):
    def test_replaying_the_json_log_gives_the_same_profits(self):
        for seed in range(20):
            result = play_round([RandomBot] * 4, seed=seed, ticks=80)
            log = json.loads(json.dumps(result.log))
            self.assertEqual(replay(log), result.profits)

    def test_log_records_the_trades(self):
        result = play_round([RandomBot] * 5, seed=3, ticks=80)
        self.assertGreater(sum(ok for *_, ok in result.log["actions"]), 0)

    def test_tampered_log_is_detected(self):
        result = play_round([RandomBot] * 4, seed=1, ticks=80)
        log = json.loads(json.dumps(result.log))
        accepted = next(a for a in log["actions"] if a[3])
        accepted[3] = False  # on prétend qu'une action acceptée a été refusée
        with self.assertRaises(ValueError):
            replay(log)


if __name__ == "__main__":
    unittest.main()
