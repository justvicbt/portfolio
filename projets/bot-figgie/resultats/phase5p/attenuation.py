"""Phase 5p, étape 2 (prototype hors du dépôt) : une atténuation par fenêtre de temps pour la lecture du site.

Choix glouton, fenêtre après fenêtre (la lecture à un instant ne dépend que des fenêtres déjà commencées), au meilleur
log-score moyen sur les manches simulées de validation de la phase 5d (figgie.learn.site_rounds, graine 52).
Puis vérification sur les 60 vraies manches, qui ne servent pas au choix.

Usage (depuis projets/bot-figgie) : PYTHONPATH=. python3 resultats/phase5p/attenuation.py MANCHES_VALIDATION
"""
import math
import statistics
import sys
import time

from figgie.bots import UNIFORM, SiteReaderBot
from figgie.learn import SITE_TEMPERS, SITE_VALID_SEED, site_rounds, state_at
from figgie.reel import load_rasmus
from figgie.signals import MarketReading, OpponentModel, price_bucket
from figgie.valuation import goal_probabilities, known_minimums

CHECKS = {0: (15, 30, 45), 1: (75, 90, 105), 2: (135, 150, 165), 3: (195, 210, 225, 239)}
REAL_TIMES = (120, 180, 225, 239)


class WindowReading(MarketReading):
    """MarketReading avec une atténuation par fenêtre (celle de l'événement, ou du consensus)."""

    def _temper(self, event):
        return self.temper[event[1][1]] if isinstance(self.temper, (list, tuple)) else self.temper

    def _add(self, event):
        player = event[1]
        key = (player, event[2], event[3], price_bucket(event[4]))
        w = self._temper(event) * self.weights.get(player, 1.0)
        if key in self._seen or w == 0:
            return
        self._seen.add(key)
        for g in self.scores:
            self.scores[g] += w * self.model.evidence(event, g)

    def posterior(self, prior, now):
        from figgie.signals import consensus_events
        scores = dict(self.scores)
        if self.model.consensus and self.players:
            for e in consensus_events(self._top, self.players, now, self.duration, self.model.windows):
                w = self._temper(e) * self.weights.get(e[1], 1.0)
                for g in scores:
                    scores[g] += w * self.model.evidence(e, g)
        logs = {g: (math.log(p) if p > 0 else -math.inf) + scores[g] for g, p in prior.items()}
        top = max(logs.values())
        exp = {g: math.exp(s - top) for g, s in logs.items()}
        total = sum(exp.values())
        return {g: v / total for g, v in exp.items()}


def sim_posterior(model, temper, hand0, events, t, duration, n):
    hand, trades, seen = state_at(hand0, events, t)
    reading = WindowReading(model, temper, duration, 0, range(n))
    reading.update(seen)
    return goal_probabilities(hand, known_minimums(trades, n), 0, goal_weights=reading.posterior(UNIFORM, t), drawn=hand0)


def log_score(model, temper, rounds, times):
    return statistics.fmean(math.log(max(sim_posterior(model, temper, h, ev, t, d, n)[g], 1e-12))
                            for h, ev, g, d, n in rounds for t in times)


def real_report(model, temper, rounds):
    out = {t: [] for t in REAL_TIMES}
    trust, session = None, None
    for r in rounds:
        me, goal = r["me"], r["goal"]
        if r.get("session") != session:
            trust, session = OpponentModel(model), r.get("session")
        others = [p for p in range(4) if p != me]
        for t in REAL_TIMES:
            seen = [e for e in r["events"] if e[0] <= t]
            bought = [e for e in seen if e[2] == "bought"]
            sold = [e for e in seen if e[2] == "sold"]
            trades = [(b[1], s[1], b[3], b[4]) for b, s in zip(bought, sold)]
            hand = dict(r["dealt"])
            for buyer, seller, suit, _ in trades:
                hand[suit] += (buyer == me) - (seller == me)
            reading = WindowReading(model, temper, r["duration"], me, range(4), trust.weights())
            reading.update(seen)
            p = goal_probabilities(hand, known_minimums(trades, 4), me, goal_weights=reading.posterior(UNIFORM, t),
                                   drawn=r["dealt"])
            out[t].append((p[goal], max(p, key=p.get) == goal, -math.log(max(p[goal], 1e-9))))
        trust.observe_round(model.round_features(r["events"], r["duration"], others, me=me), goal, me=None)
    return {t: tuple(statistics.fmean(x[i] for x in v) for i in range(3)) for t, v in out.items()}


def main():
    n_valid = int(sys.argv[1])
    model, base = SiteReaderBot.model()
    start = time.time()
    valid = site_rounds(n_valid, SITE_VALID_SEED)
    print(f"{n_valid} manches de validation simulées, {time.time() - start:.0f} s", file=sys.stderr, flush=True)
    chosen, step, total = [], 0, len(CHECKS) * len(SITE_TEMPERS)
    for w, times in CHECKS.items():
        scores = {}
        for tp in SITE_TEMPERS:
            temper = chosen + [tp] + [tp] * (3 - w)
            scores[tp] = log_score(model, temper, valid, times)
            step += 1
            el = time.time() - start
            print(f"{step}/{total} essais, {el / 60:.0f} min écoulées, fin dans ~{el / step * (total - step) / 60:.0f} min",
                  file=sys.stderr, flush=True)
        best = max(scores, key=scores.get)
        chosen.append(best)
        print(f"fenêtre {w} : " + ", ".join(f"{tp} -> {s:+.3f}" for tp, s in scores.items()) + f" ; retenu {best}")
    print(f"\nAtténuations retenues : {chosen} (aujourd'hui : {base} partout)")
    rounds = load_rasmus()
    for label, temper in (("aujourd'hui", base), ("par fenêtre", chosen)):
        rep = real_report(model, temper, rounds)
        print(f"Vraies manches, {label} : " + " ; ".join(f"{t} s : {p:.2f}, {top:.0%}, {ll:.3f}" for t, (p, top, ll) in rep.items()))


if __name__ == "__main__":
    main()
