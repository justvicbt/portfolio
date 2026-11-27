"""Phase 5s, critère fixé d'avance : la lecture du site apprise sur des tables avec le Hard v3 fait-elle mieux sur les
60 vraies manches de Rasmus (qui ne servent jamais à apprendre) que celle de la phase 5d ?
Il faut, à 180, 225 et 239 s : une perte log plus basse, et une part de manches où la vraie couleur est en tête au
moins égale.

Usage (depuis projets/bot-figgie) : PYTHONPATH=. python3 resultats/phase5s/mesure_reelle.py
"""
from figgie.reel import goal_calibration, load_rasmus

TIMES = (60, 120, 180, 225, 239)
CRITERION = (180, 225, 239)

rounds = load_rasmus()
old = goal_calibration(rounds, TIMES)["lecture site"]
new = goal_calibration(rounds, TIMES, signals_file="signaux_site_v3.json")["lecture site"]
print("Vraies manches : P moyenne de la vraie couleur / part en tête / perte log")
for label, by_t in (("modèle de la phase 5d (Hard 5c)", old), ("modèle appris avec le Hard v3", new)):
    print(f"  {label:32s} " + "   ".join(f"{t} s : {p:.2f} / {acc:.0%} / {ll:.3f}" for t, (p, acc, ll) in by_t.items()))
ok = all(new[t][2] < old[t][2] and new[t][1] >= old[t][1] for t in CRITERION)
print(f"\nCritère (perte log plus basse et part en tête au moins égale à {CRITERION} s) : {'rempli' if ok else 'non rempli'}")
