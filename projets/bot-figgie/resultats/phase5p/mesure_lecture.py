"""Phase 5p, étape 1 : la lecture du site d'aujourd'hui et le consensus brut, en fin de manche.

Vraies manches : les 60 de Rasmus (figgie.reel.goal_calibration, « lecture site », confiance apprise dans la session).
Manches simulées : v4c_achat au siège 0 et des Hard recalés, règle du site, 4 ou 5 joueurs (graine 53, jamais
utilisée pour apprendre), lecture vue du siège 0 sans confiance apprise.
Consensus brut : la couleur où le plus bas des plus hauts prix d'achat des autres joueurs est le plus haut.

Usage (depuis projets/bot-figgie) : PYTHONPATH=. python3 resultats/phase5p/mesure_lecture.py MANCHES_SIMULEES
"""
import math
import random
import statistics
import sys
import time
from multiprocessing import Pool

from figgie.bots import SiteReaderBot
from figgie.engine import play_round
from figgie.evaluate import CANDIDATES
from figgie.learn import site_posterior
from figgie.reel import goal_calibration, load_rasmus
from figgie.signals import top_bids

TIMES = (120, 180, 225, 239)


def consensus_top(events, players, t):
    top = top_bids([e for e in events if e[0] <= t], players)
    cons = {s: min(top.get((p, s), 0) for p in players) for s in "SCHD"}
    best = max(cons.values())
    leaders = [s for s in "SCHD" if cons[s] == best]
    return leaders  # ex aequo possibles


def sim(i):
    seed = 53 * 1_000_000 + i
    n = random.Random(seed).choice((4, 5))
    bots = [CANDIDATES["v4c_achat"]] + [CANDIDATES["hard_simule_v2"]] * (n - 1)
    res = play_round(bots, seed=seed, single_quote=True)
    model, temper = SiteReaderBot.model()
    out = []
    for t in TIMES:
        p = site_posterior(model, temper, res.log["hands"][0], res.events, t, res.log["duration"], n)
        g = res.log["goal"]
        leaders = consensus_top(res.events, range(1, n), t)
        out.append((t, p[g], max(p, key=p.get) == g, -math.log(max(p[g], 1e-9)), (g in leaders) / len(leaders)))
    return out


def main():
    n_sim = int(sys.argv[1])
    rounds = load_rasmus()
    real = goal_calibration(rounds, times=TIMES, per_round=True)["lecture site"]
    print("Vraies manches (60) : P(vrai objectif), part en tête, perte log ; consensus brut en tête")
    for t in TIMES:
        rows = real[t]
        cons = statistics.fmean((r["goal"] in (L := consensus_top(r["events"], [p for p in range(4) if p != r["me"]], t))) / len(L)
                                for r in rounds)
        print(f"  {t:3d} s : lecture {statistics.fmean(x[0] for x in rows):.2f}, {statistics.fmean(x[1] for x in rows):.0%}, "
              f"{statistics.fmean(x[2] for x in rows):.3f} ; consensus {cons:.0%}")
    start, res = time.time(), []
    with Pool() as pool:
        for done, r in enumerate(pool.imap_unordered(sim, range(n_sim), chunksize=4), 1):
            res.append(r)
            if done % 50 == 0 or done == n_sim:
                el = time.time() - start
                print(f"{done}/{n_sim} manches simulées, {el / 60:.0f} min écoulées, fin dans ~{el / done * (n_sim - done) / 60:.0f} min",
                      file=sys.stderr, flush=True)
    print(f"\nManches simulées ({n_sim}, Hard recalés)")
    for k, t in enumerate(TIMES):
        rows = [r[k] for r in res]
        print(f"  {t:3d} s : lecture {statistics.fmean(x[1] for x in rows):.2f}, {statistics.fmean(x[2] for x in rows):.0%}, "
              f"{statistics.fmean(x[3] for x in rows):.3f} ; consensus {statistics.fmean(x[4] for x in rows):.0%}")


if __name__ == "__main__":
    main()
