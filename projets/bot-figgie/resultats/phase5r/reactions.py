"""Phase 5r, étape 1 : à quoi réagissent les bots Hard du site, et les nôtres ?

Réaction étudiée : un bot Hard propose dans une couleur un prix d'achat plus haut que tout ce qu'il y avait proposé
jusque-là dans la manche (« nouveau record »). Déclencheurs, dans la même couleur, par un autre joueur :
échange à 1-3 $, à 4-6 $, à 7 $ ou plus ; offre de vente affichée ; retrait ; offre d'achat d'un autre au-dessus de
tout ce qui avait été proposé dans la couleur. Pour chaque déclencheur, je compte les records de chaque autre bot Hard
dans les 10 s qui suivent, et je divise par ce qu'on attendrait au hasard : le rythme de records de ce bot, dans cette
couleur, dans cette minute de la manche. Un rapport de 1 veut dire « aucune réaction ».
Je sépare aussi les déclencheurs selon que la couleur est l'objectif ou non : ça dit si le déclencheur porte de
l'information sur l'objectif.

Vraies manches : les 60 de Rasmus (bots Hard = les trois autres sièges). Simulées : v4c_achat et trois Hard recalés,
règle du site, 4 joueurs, 200 manches (graine 9), le bot au siège 0 comme celui de Rasmus.

Usage (depuis projets/bot-figgie) : PYTHONPATH=. python3 resultats/phase5r/reactions.py
"""
import sys
from collections import defaultdict

from figgie.engine import play_round
from figgie.evaluate import CANDIDATES
from figgie.reel import load_rasmus

WINDOW = 10.0


def trigger_kind(e, events, i, table_top):
    t, p, kind, s, price = e
    if kind == "bought":
        return "échange 1-3 $" if price <= 3 else "échange 4-6 $" if price <= 6 else "échange 7 $ et plus"
    if kind == "ask":
        return "offre de vente"
    if kind == "cancel":
        return "retrait"
    if kind == "bid" and price > table_top.get(s, 0):
        return "offre d'achat record de la table"
    return None


def analyse(rounds):
    """{(déclencheur, objectif ?): [records observés, records attendus, déclencheurs]}"""
    out = defaultdict(lambda: [0.0, 0.0, 0])
    for r in rounds:
        events, hard, goal, d = r["events"], set(r["hard"]), r["goal"], r["duration"]
        records = defaultdict(list)  # (bot, couleur) -> instants de ses records
        best = {}
        for t, p, kind, s, price in events:
            if kind == "bid" and p in hard and price > best.get((p, s), 0):
                best[p, s] = price
                records[p, s].append(t)
        rate = {}  # (bot, couleur, minute) -> records par seconde
        for (p, s), ts in records.items():
            for m in range(4):
                rate[p, s, m] = sum(m * 60 <= t < (m + 1) * 60 for t in ts) / 60
        table_top = {}
        for i, e in enumerate(events):
            t, who, kind, s, price = e
            k = trigger_kind(e, events, i, table_top)
            if kind == "bid":
                table_top[s] = max(table_top.get(s, 0), price)
            if k is None or t + WINDOW > d:
                continue
            m = min(3, int(t // 60))
            for p in hard:
                if p == who or (kind == "bought" and events[i + 1][1] == p):
                    continue  # pas le joueur qui déclenche, ni le vendeur de l'échange
                obs = sum(t < x <= t + WINDOW for x in records[p, s])
                exp = rate.get((p, s, m), 0.0) * WINDOW
                cell = out[k, s == goal]
                cell[0] += obs
                cell[1] += exp
                cell[2] += 1
    return out


def report(label, out):
    print(f"\n{label} : records d'offre d'achat des bots Hard dans les 10 s, rapportés au hasard")
    print(f"  {'déclencheur':34s} {'objectif':>22s} {'autre couleur':>22s}")
    for k in ("échange 1-3 $", "échange 4-6 $", "échange 7 $ et plus", "offre de vente", "retrait",
              "offre d'achat record de la table"):
        cells = []
        for g in (True, False):
            obs, exp, n = out[k, g]
            cells.append(f"{obs / exp if exp else float('nan'):5.2f} ({n:5d})")
        print(f"  {k:34s} {cells[0]:>22s} {cells[1]:>22s}")


def simulated(n_rounds):
    rounds = []
    for g in range(n_rounds):
        res = play_round([CANDIDATES["v4c_achat"]] + [CANDIDATES["hard_simule_v2"]] * 3, seed=9_000_000 + g,
                         single_quote=True)
        rounds.append({"events": res.events, "hard": [1, 2, 3], "goal": res.log["goal"], "duration": res.log["duration"]})
        if (g + 1) % 50 == 0:
            print(f"{g + 1}/{n_rounds} manches simulées", file=sys.stderr, flush=True)
    return rounds


def main():
    report("Vraies manches (60)", analyse(load_rasmus()))
    report("Hard recalés (200 manches simulées)", analyse(simulated(200)))


if __name__ == "__main__":
    main()
