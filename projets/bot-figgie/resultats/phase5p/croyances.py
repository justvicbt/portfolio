"""Phase 5p, étape 1 : ce que v4c_achat croit des autres, comparé à la vérité, contre des Hard recalés.

À 120, 180 et 225 s (premier regard du bot après chaque instant), je note :
  - P(vraie couleur objectif) selon le bot (main, cartes connues des autres et lecture du marché), et selon la lecture
    du marché seule ;
  - le nombre de cartes objectif qu'il attend chez le vrai meneur parmi ses rivaux (objectif supposé connu, mains
    cachées réparties au hasard dans les places inconnues, comme son Monte Carlo), et le vrai nombre ;
  - le nombre de cartes objectif qu'il a lui-même.
Séparément pour les manches qu'il finit à égalité de majorité, et pour toutes.

Usage (depuis projets/bot-figgie) : PYTHONPATH=. python3 resultats/phase5p/croyances.py DONNES
"""
import sys
import time
from collections import defaultdict
from multiprocessing import Pool

from figgie.adapt import BuyTimedV4cBot
from figgie.engine import Market, play_match
from figgie.evaluate import CANDIDATES
from figgie.valuation import goal_probabilities, initial_hand, known_minimums

SEED, ROUNDS, MOMENTS = 9, 10, (120, 180, 225)
RECORDS = []


class Spy(BuyTimedV4cBot):
    def __init__(self):
        super().__init__()
        RECORDS.append([])
        self._next = 0

    def act(self, view, rng):
        action = super().act(view, rng)
        if self._next < len(MOMENTS) and view.time >= MOMENTS[self._next] and self._market is not None:
            mins = self._mins if self.ask_counting else known_minimums(view.trades, view.n_players)
            drawn = initial_hand(view.hand, view.trades, view.seat)
            RECORDS[-1].append(dict(moment=MOMENTS[self._next], t=view.time, hand=dict(view.hand),
                                    mins=[dict(m) for m in mins], counts=list(view.card_counts),
                                    p_bot=goal_probabilities(view.hand, mins, view.seat, self._market, drawn),
                                    p_market=dict(self._market)))
            while self._next < len(MOMENTS) and view.time >= MOMENTS[self._next]:
                self._next += 1
        return action


def hands_at(log, t):
    market = Market(log["hands"], log.get("single_quote", False))
    for ta, seat, action, ok, _ in log["actions"]:
        if ta > t:
            break
        if ok:
            market.apply(seat, action)
    return market.hands


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
        size = sum(h[goal] for h in log["hands"])
        final = [h[goal] for h in hands_at(log, 1e9)]
        tie = final[me] == max(final[:me] + final[me + 1:])
        for r in records:
            now = [h[goal] for h in hands_at(log, r["t"])]
            rivals = [j for j in range(n) if j != me]
            leader = max(rivals, key=lambda j: now[j])
            known = r["hand"][goal] + sum(r["mins"][j][goal] for j in rivals)
            free = {j: r["counts"][j] - sum(r["mins"][j].values()) for j in rivals}
            spread = (size - known) / sum(free.values()) if sum(free.values()) else 0.0
            expected = r["mins"][leader][goal] + free[leader] * spread
            all_true = sum(now[j] for j in rivals) / len(rivals)
            all_exp = sum(r["mins"][j][goal] + free[j] * spread for j in rivals) / len(rivals)
            err = sum(abs(now[j] - r["mins"][j][goal] - free[j] * spread) for j in rivals) / len(rivals)
            rows.append(dict(tie=tie, moment=r["moment"], p_bot=r["p_bot"][goal], p_market=r["p_market"][goal],
                             top_bot=max(r["p_bot"], key=r["p_bot"].get) == goal,
                             lead_true=now[leader], lead_expected=expected, lead_known=r["mins"][leader][goal],
                             mine=now[me], all_true=all_true, all_exp=all_exp, err=err))
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
        print(f"\n{n} joueurs")
        for label, keep in (("manches finies à égalité", True), ("toutes les manches", None)):
            print(f"  {label}")
            for moment in MOMENTS:
                rs = [r for r in rows[n] if r["moment"] == moment and (keep is None or r["tie"])]
                if not rs:
                    continue
                k = len(rs)
                mean = lambda key: sum(r[key] for r in rs) / k
                print(f"    {moment:3d} s ({k:4d}) : P(vrai objectif) bot {mean('p_bot'):.2f}, marché seul {mean('p_market'):.2f}, "
                      f"en tête chez le bot {mean('top_bot'):.0%} ; meneur : vrai {mean('lead_true'):.2f}, "
                      f"attendu {mean('lead_expected'):.2f} (dont connu {mean('lead_known'):.2f}) ; le bot en a {mean('mine'):.2f} ; "
                      f"rival moyen : vrai {mean('all_true'):.2f}, attendu {mean('all_exp'):.2f}, erreur {mean('err'):.2f}")


if __name__ == "__main__":
    main()
