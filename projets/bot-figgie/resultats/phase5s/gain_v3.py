"""Phase 5s, étape 1 : d'où viennent les 35 $ par manche que la v4c « achat » gagne contre trois Hard v3 ?

Le gain d'un joueur se découpe exactement en trois parts :
- la donne : 10 $ par carte objectif reçue, moins la mise (-50 $ à 4 joueurs) ;
- les échanges, chaque carte comptée à sa valeur de fin (10 $ si objectif, 0 sinon) : acheter l'objectif à p rapporte
  10 - p, vendre une autre couleur à p rapporte p, etc. ;
- la prime de majorité : la part du reste du pot.
Mêmes parties (graines 9 000 000 + g, 10 manches, règle du site, v4c « achat » au siège 0) contre trois Hard recalés
puis contre trois Hard v3 : la donne est la même, l'écart vient des deux autres parts.

Usage (depuis projets/bot-figgie) : PYTHONPATH=. python3 resultats/phase5s/gain_v3.py 500
"""
import statistics
import sys
import time
from collections import defaultdict
from multiprocessing import Pool

from figgie.engine import GOAL_CARD_VALUE, POT, START_CASH, play_round, score
from figgie.evaluate import CANDIDATES

ROUNDS = 10


def one_match(job):
    hard, g = job
    bots = [CANDIDATES["v4c_achat"]] + [CANDIDATES[hard]] * 3
    memories = [{} for _ in bots]
    out = []
    for r in range(ROUNDS):
        seed = 9_000_000 + g
        res = play_round(bots, seed=seed if r == 0 else f"{seed}:{r}", memories=memories, single_quote=True)
        goal, hands0 = res.log["goal"], res.log["hands"]
        n = len(bots)
        cell = defaultdict(float)
        deal = GOAL_CARD_VALUE * hands0[0][goal] - POT / n
        held = hands0[0][goal]
        ev = res.events
        for i, (t, p, kind, s, price) in enumerate(ev):
            if kind != "bought":
                continue
            seller = ev[i + 1][1]
            if 0 not in (p, seller):
                continue
            worth = GOAL_CARD_VALUE if s == goal else 0
            side = "achat" if p == 0 else "vente"
            pnl = worth - price if p == 0 else price - worth
            what = "objectif" if s == goal else "autre"
            m = min(3, int(t // 60))
            cell[f"{what} {side} : gain"] += pnl
            cell[f"{what} {side} : cartes"] += 1
            cell[f"{what} {side} : somme des prix"] += price
            cell[f"{what} {side} : gain minute {m + 1}"] += pnl
            if s == goal:
                held += 1 if p == 0 else -1
        counts = [h[goal] for h in hands0]
        # nombres finaux d'objectif de chacun, depuis le fil
        final = list(counts)
        for i, (t, p, kind, s, price) in enumerate(ev):
            if kind == "bought" and s == goal:
                final[p] += 1
                final[ev[i + 1][1]] -= 1
        assert final[0] == held
        share = score(final)[0] - GOAL_CARD_VALUE * final[0]
        trades = sum(v for k, v in cell.items() if k.endswith(": gain"))
        assert abs(deal + trades + share - res.profits[0]) < 1e-6, (deal, trades, share, res.profits[0])
        cell["donne"] = deal
        cell["échanges"] = trades
        cell["prime de majorité"] = share
        cell["gain total"] = res.profits[0]
        cell["objectif : cartes du bot, donne"] = counts[0]
        cell["objectif : cartes du bot, fin"] = final[0]
        cell["objectif : meilleur rival, donne"] = max(counts[1:])
        cell["objectif : meilleur rival, fin"] = max(final[1:])
        cell["objectif : cartes des 3 Hard entre eux échangées"] = sum(
            1 for i, e in enumerate(ev) if e[2] == "bought" and e[3] == goal and 0 not in (e[1], ev[i + 1][1]))
        cell["seul en tête"] = float(final[0] > max(final[1:]))
        cell["à égalité en tête"] = float(final[0] == max(final[1:]))
        out.append(dict(cell))
    return hard, out


def main():
    n = int(sys.argv[1])
    jobs = [(h, g) for h in ("hard_simule_v2", "hard_simule_v3") for g in range(n)]
    res = defaultdict(list)
    start = time.time()
    with Pool() as pool:
        for k, (hard, rounds) in enumerate(pool.imap_unordered(one_match, jobs), 1):
            res[hard] += rounds
            el = time.time() - start
            print(f"{k}/{len(jobs)} parties, {el / 60:.0f} min écoulées, fin dans ~{el / k * (len(jobs) - k) / 60:.0f} min",
                  file=sys.stderr, flush=True)
    keys = sorted({k for rs in res.values() for r in rs for k in r},
                  key=lambda k: (k not in ("gain total", "donne", "échanges", "prime de majorité"), k))
    print(f"{n} parties de {ROUNDS} manches, v4c « achat » au siège 0, moyenne par manche")
    print(f"{'':40s} {'Hard recalés':>14s} {'Hard v3':>14s}")
    for k in keys:
        row = []
        for h in ("hard_simule_v2", "hard_simule_v3"):
            vals = [r.get(k, 0.0) for r in res[h]]
            row.append(f"{statistics.mean(vals):14.2f}")
        print(f"{k:40s} {' '.join(row)}")
    for h in ("hard_simule_v2", "hard_simule_v3"):
        tot = [r["gain total"] for r in res[h]]
        print(f"{h} : gain total {statistics.mean(tot):.2f} ± {1.96 * statistics.stdev(tot) / len(tot) ** 0.5:.2f}")


if __name__ == "__main__":
    main()
