"""Diagnostic de regroupement, suite : dans les manches que v4c_achat finit à égalité de majorité, que valait pour lui
la carte objectif offerte moins cher que ce qu'elle aurait rapporté ?

Pour chaque offre de vente d'un autre joueur sur l'objectif, vue après 120 s, je compare quatre valeurs d'achat de
cette carte (à ce vendeur), au même instant :
  A. celle du bot (poids du temps à l'achat, lecture du marché, mains cachées tirées au hasard) ;
  B. la même avec la majorité comptée en entier (sans le poids du temps) ;
  C. B avec l'objectif connu (seules les mains des autres restent cachées) ;
  D. le gain exact d'une carte de plus, mains de tous connues, si plus rien ne s'échange.
A -> B : effet du poids ; B -> C : effet de l'objectif incertain ; C -> D : effet des mains cachées.
Le bot prend l'offre si prix <= A - marge.

Usage (depuis projets/bot-figgie) : PYTHONPATH=. python3 resultats/phase5p/valeur.py DONNES
"""
import random
import sys
import time
from collections import defaultdict
from multiprocessing import Pool

from figgie.adapt import BuyTimedV4cBot
from figgie.engine import Market, payout, play_match
from figgie.evaluate import CANDIDATES
from figgie.valuation import initial_hand, known_minimums, marginal_values

SEED, ROUNDS = 9, 10
RECORDS = []  # une liste par manche (un bot neuf par manche)


class Spy(BuyTimedV4cBot):
    def __init__(self):
        super().__init__()
        RECORDS.append([])
        self._last = {}

    def act(self, view, rng):
        action = super().act(view, rng)
        if view.time >= 120 and self._values is not None:
            for s in self._values:
                ask = view.best(s, "ask")
                if not ask or ask[1] == view.seat or self._last.get(s) == ask:
                    continue
                self._last[s] = ask
                mins = self._mins if self.ask_counting else known_minimums(view.trades, view.n_players)
                edge = None if self.edge is None else self._over_time(view, self.edge, self.edge_late)
                RECORDS[-1].append(dict(t=view.time, suit=s, price=ask[0], seller=ask[1], a=self._values[s][0][ask[1]],
                                        edge=edge, hand=dict(view.hand), seat=view.seat,
                                        counts=list(view.card_counts), mins=[dict(m) for m in mins],
                                        market=dict(self._market), drawn=initial_hand(view.hand, view.trades, view.seat)))
        return action


def counts_at(log, t):
    market = Market(log["hands"], log.get("single_quote", False))
    for ta, seat, action, ok, _ in log["actions"]:
        if ta > t:
            break
        if ok:
            market.apply(seat, action)
    return market


def job(args):
    deal, n = args
    RECORDS.clear()
    me = deal % n
    bots = [CANDIDATES["hard_simule_v2"]] * n
    bots[me] = Spy
    match = play_match(bots, seed=SEED * 1_000_000 + deal, rounds=ROUNDS, single_quote=True)
    rows = []
    for log, records in zip(match.logs, RECORDS):
        goal = log["goal"]
        final = [h[goal] for h in counts_at(log, 1e9).hands]
        m, others = final[me], final[:me] + final[me + 1:]
        if m != max(others):
            continue  # seulement les manches finies à égalité
        for r in records:
            if r["suit"] != goal:
                continue
            kw = dict(goal_weights=r["market"], drawn=r["drawn"], majority_weight=1.0, weight_sell=False)
            b = marginal_values(r["hand"], r["seat"], r["counts"], r["mins"], random.Random(1), 300, **kw)[goal][0][r["seller"]]
            sure = {s: (1.0 if s == goal else 1e-9) for s in r["market"]}
            kw["goal_weights"] = sure
            c = marginal_values(r["hand"], r["seat"], r["counts"], r["mins"], random.Random(1), 300, **kw)[goal][0][r["seller"]]
            now = [h[goal] for h in counts_at(log, r["t"]).hands]
            mine, oth = now[me], now[:me] + now[me + 1:]
            after = list(oth)
            j = r["seller"] if r["seller"] < me else r["seller"] - 1
            after[j] -= 1
            d = payout(mine + 1, after) - payout(mine, oth)
            rows.append(dict(price=r["price"], a=r["a"], b=b, c=c, d=d, edge=r["edge"], t=r["t"]))
    return n, rows


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
        rs = rows[n]
        print(f"\n{n} joueurs : {len(rs)} offres de vente sur l'objectif, après 120 s, dans les manches finies à égalité")
        for label, sel in (("toutes", rs), ("moins chères que le gain exact D", [r for r in rs if r["price"] < r["d"]])):
            if not sel:
                continue
            k = len(sel)
            mean = lambda key: sum(r[key] for r in sel) / k
            edges = [r["edge"] for r in sel if r["edge"] is not None]
            print(f"  {label} ({k}) : prix {mean('price'):.2f} $, A bot {mean('a'):.2f}, B sans poids {mean('b'):.2f}, "
                  f"C objectif connu {mean('c'):.2f}, D exact {mean('d'):.2f}, marge {sum(edges) / len(edges) if edges else float('nan'):.2f}")
            print(f"      le bot l'aurait prise (prix <= A - marge) : {sum(r['edge'] is not None and r['price'] <= r['a'] - r['edge'] for r in sel) / k:.0%} ; "
                  f"avec B : {sum(r['edge'] is not None and r['price'] <= r['b'] - r['edge'] for r in sel) / k:.0%} ; "
                  f"avec C : {sum(r['edge'] is not None and r['price'] <= r['c'] - r['edge'] for r in sel) / k:.0%}")


if __name__ == "__main__":
    main()
