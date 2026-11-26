"""Phase 5q : le Hard recalé avec d'autres forces de lecture du marché (read) et valeurs de l'objectif (goal_worth).
Consensus des Hard à 120, 180 et 239 s, et écart avec le site sans le consensus (figgie.calibrate), 90 manches, graine 32.

Usage (depuis projets/bot-figgie) : python3 resultats/phase5q/sonde_lecture.py
"""
import sys

from figgie.bots import HardBotV2
from figgie.calibrate import distance, measures, simulate
from figgie.reel import load_rasmus

real = measures(load_rasmus())
base = {k: getattr(HardBotV2, k) for k in ("base", "goal_worth", "margin", "margin_power", "pace", "noise", "open_ask", "read")}
grid = [(r, gw) for r in (0, 0.2, 0.4, 0.6, 0.8, 1.2) for gw in (16, 30)]
print(f"site : consensus {[round(x, 2) for x in real['consensus']]}")
for k, (r, gw) in enumerate(grid, 1):
    st = simulate({**base, "read": r, "goal_worth": gw}, 90, 32)
    print(f"read {r} goal_worth {gw} : consensus {[round(x, 2) for x in st['consensus']]}, "
          f"écart sans consensus {distance(st, real, True, False):.1f}, avec {distance(st, real, True, True):.1f}")
    print(f"{k}/{len(grid)} réglages", file=sys.stderr, flush=True)
