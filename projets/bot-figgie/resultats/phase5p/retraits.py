"""Phase 5p : les bots Hard du site retirent-ils leurs offres ? Journaux de Rasmus, puis nos Hard recalés.

Usage (depuis projets/bot-figgie) : PYTHONPATH=. python3 resultats/phase5p/retraits.py
"""
from collections import Counter

from figgie.engine import play_round
from figgie.evaluate import CANDIDATES
from figgie.reel import load_rasmus

rounds = load_rasmus()
cancels, quotes, with_cancel, one_side, both_sides, times = Counter(), 0, 0, 0, 0, []
for r in rounds:
    me, n = r["me"], 0
    keys = Counter()
    for i, (t, p, kind, suit, _price) in enumerate(r["events"]):
        if p == me:
            continue
        if kind in ("bid", "ask"):
            quotes += 1
        if kind == "cancel":
            cancels["achat" if i in r["bid_cancels"] else "vente"] += 1
            keys[t, p, suit] += 1
            times.append(t)
            n += 1
    with_cancel += n > 0
    one_side += sum(v == 1 for v in keys.values())
    both_sides += sum(v >= 2 for v in keys.values())
times.sort()
print(f"Vrais bots Hard, {len(rounds)} manches : {sum(cancels.values())} retraits ({dict(cancels)}), "
      f"{sum(cancels.values()) / quotes:.2%} de leurs {quotes} cotations, dans {with_cancel} manches")
print(f"  d'un seul côté : {one_side}, des deux côtés au même instant : {both_sides} ; "
      f"instant médian {times[len(times) // 2]} s")
sim, sim_quotes = Counter(), 0
for d in range(60):
    res = play_round([CANDIDATES["v4c_achat"]] + [CANDIDATES["hard_simule_v2"]] * 3, seed=9_000_000 + d, single_quote=True)
    for _t, seat, a, ok, _ in res.log["actions"]:
        if seat and ok:
            sim_quotes += a[0] in ("bid", "ask")
            if a[0] == "cancel":
                sim["deux côtés" if len(a) == 2 else "un côté"] += 1
print(f"Hard recalés, 60 manches simulées (v4c_achat et 3 Hard, graine 9) : retraits {dict(sim)}, {sim_quotes} cotations")
