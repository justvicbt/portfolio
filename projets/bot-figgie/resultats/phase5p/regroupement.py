"""Diagnostic de regroupement (après la phase 5o) : v4c_achat contre des Hard recalés, règle du site.

Pour chaque manche, la position finale du bot dans la couleur objectif face au meilleur rival :
seul en tête, à égalité, une carte derrière, ou plus loin. Pour les manches à égalité ou à une carte,
ce qu'aurait rapporté une carte objectif de plus (prise au meneur ou à un autre joueur), et si une
offre de vente sur l'objectif, d'un autre joueur, a été affichée sous ce prix sans qu'il la prenne.

Usage (depuis projets/bot-figgie) : PYTHONPATH=. python3 resultats/phase5p/regroupement.py DONNES
"""
import sys
import time
from collections import defaultdict
from multiprocessing import Pool

from figgie.engine import Market, payout, play_match
from figgie.evaluate import CANDIDATES

SEED, ROUNDS = 9, 10


def gain_one_more(m, others, src):
    after = list(others)
    after[src] -= 1
    return payout(m + 1, after) - payout(m, others)


def analyse(log, me):
    market = Market(log["hands"], log.get("single_quote", False))
    for _t, seat, action, ok, _seen in log["actions"]:
        if ok:
            market.apply(seat, action)
    goal = log["goal"]
    counts = [h[goal] for h in market.hands]
    m = counts[me]
    others = counts[:me] + counts[me + 1:]
    best = max(others)
    cat = "seul en tête" if m > best else "égalité" if m == best else "une carte derrière" if m == best - 1 else "plus loin"
    sold = sum(1 for b, s_, suit, _ in market.trades if s_ == me and suit == goal)
    bought = sum(1 for b, s_, suit, _ in market.trades if b == me and suit == goal)
    out = {"cat": cat, "goal_size": sum(counts), "m": m, "profit": log["profits"][me], "sold": sold, "bought": bought,
           "dealt": log["hands"][me][goal]}
    if cat in ("égalité", "une carte derrière"):
        leader = others.index(best)
        from_leader = gain_one_more(m, others, leader)
        donors = [i for i, c in enumerate(others) if c > 0 and i != leader]
        from_other = max((gain_one_more(m, others, i) for i in donors), default=None)
        asks = [(t, action[2]) for t, seat, action, ok, _ in log["actions"]
                if ok and seat != me and action[0] == "ask" and action[1] == goal]
        bids = [action[2] for t, seat, action, ok, _ in log["actions"]
                if ok and seat == me and action[0] == "bid" and action[1] == goal]
        cheapest = min((p for t, p in asks if t >= 120), default=None)  # seconde moitié : l'objectif est mieux connu
        out.update(from_leader=from_leader, from_other=from_other, cheapest_ask=cheapest,
                   max_bid=max(bids, default=None),
                   missed=cheapest is not None and cheapest < max(from_leader, from_other or 0))
    return out


def job(args):
    deal, n = args
    me = deal % n
    bots = [CANDIDATES["hard_simule_v2"]] * n
    bots[me] = CANDIDATES["v4c_achat"]
    match = play_match(bots, seed=SEED * 1_000_000 + deal, rounds=ROUNDS, single_quote=True)
    return n, [analyse(log, me) for log in match.logs]


def report(rows, n):
    print(f"\n{n} joueurs : {len(rows)} manches")
    by = defaultdict(list)
    for r in rows:
        by[r["cat"]].append(r)
    for cat in ("seul en tête", "égalité", "une carte derrière", "plus loin"):
        rs = by[cat]
        if not rs:
            continue
        k = len(rs)
        print(f"  {cat:20s} {k / len(rows):6.1%}  gain moyen {sum(r['profit'] for r in rs) / k:+7.2f} $ ; "
              f"objectif reçu {sum(r['dealt'] for r in rs) / k:.2f}, acheté {sum(r['bought'] for r in rs) / k:.2f}, "
              f"vendu {sum(r['sold'] for r in rs) / k:.2f}, gardé {sum(r['m'] for r in rs) / k:.2f}")
        if cat in ("égalité", "une carte derrière"):
            fl = sum(r["from_leader"] for r in rs) / len(rs)
            fo = [r["from_other"] for r in rs if r["from_other"] is not None]
            missed = [r for r in rs if r["missed"]]
            print(f"      une carte de plus, prise au meneur : {fl:+.2f} $ en moyenne ; à un autre : "
                  f"{sum(fo) / len(fo) if fo else float('nan'):+.2f} $ ({len(fo)} manches)")
            print(f"      offre de vente d'un autre sous ce gain, affichée après 120 s : {len(missed)} manches "
                  f"({len(missed) / len(rows):.1%} de toutes)")
            if missed:
                print(f"      dans ces manches : offre la moins chère {sum(r['cheapest_ask'] for r in missed) / len(missed):.2f} $, "
                      f"meilleure offre d'achat du bot {sum(r['max_bid'] or 0 for r in missed) / len(missed):.2f} $")
    for size in sorted({r["goal_size"] for r in rows}):
        rs = [r for r in rows if r["goal_size"] == size]
        tie = sum(r["cat"] == "égalité" for r in rs) / len(rs)
        short = sum(r["cat"] == "une carte derrière" for r in rs) / len(rs)
        print(f"  objectif à {size} cartes : {len(rs)} manches, égalité {tie:.1%}, une carte derrière {short:.1%}")


def main():
    deals = int(sys.argv[1])
    jobs = [(d, n) for n in (4, 5) for d in range(deals)]
    rows = defaultdict(list)
    start = time.time()
    with Pool() as pool:
        for done, (n, part) in enumerate(pool.imap_unordered(job, jobs), 1):
            rows[n].extend(part)
            el = time.time() - start
            print(f"{done}/{len(jobs)} parties, {el / 60:.0f} min écoulées, fin dans ~{el / done * (len(jobs) - done) / 60:.0f} min",
                  file=sys.stderr, flush=True)
    for n in (4, 5):
        report(rows[n], n)


if __name__ == "__main__":
    main()
