"""Phase 5r : chaque bot Hard pris seul. À chaque instant, la couleur où il a proposé son plus haut prix d'achat
(depuis le début, ou dans les 30 dernières secondes) est-elle l'objectif ? Égalité entre k couleurs : 1/k.

Usage (depuis projets/bot-figgie) : PYTHONPATH=. python3 resultats/phase5r/individuel.py
"""
import statistics
import sys

from figgie.engine import play_round
from figgie.evaluate import CANDIDATES
from figgie.reel import load_rasmus

TIMES = (60, 120, 180, 239)


def hits(rounds, recent=None):
    out = {t: [] for t in TIMES}
    for r in rounds:
        for p in r["hard"]:
            for t in TIMES:
                top = {s: 0 for s in "SCHD"}
                for te, who, kind, s, price in r["events"]:
                    if te > t:
                        break
                    if who == p and kind == "bid" and (recent is None or te > t - recent):
                        top[s] = max(top[s], price)
                lead = [s for s in top if top[s] == max(top.values())]
                out[t].append((r["goal"] in lead) / len(lead))
    return [round(statistics.fmean(out[t]), 2) for t in TIMES]


def sim(n, hard="hard_simule_v2"):
    rounds = []
    for g in range(n):
        res = play_round([CANDIDATES["v4c_achat"]] + [CANDIDATES[hard]] * 3, seed=9_000_000 + g, single_quote=True)
        rounds.append({"events": res.events, "hard": [1, 2, 3], "goal": res.log["goal"]})
    return rounds


real, simulated, v3 = load_rasmus(), sim(200), sim(200, "hard_simule_v3")
for label, rounds in (("vraies manches", real), ("Hard recalés", simulated), ("Hard v3", v3)):
    print(f"{label} : plus haut prix depuis le début {hits(rounds)} ; sur les 30 dernières s {hits(rounds, 30)}  (à {TIMES} s)")
