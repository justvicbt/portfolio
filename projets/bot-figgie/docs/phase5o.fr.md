# Phase 5o : chercher un exploiteur de la v4c « achat »

*English version: [phase5o.en.md](phase5o.en.md)*

En phase 5n, la v4c « achat » est devenue le bot de référence. Elle passe la règle d'entrée, mais cette règle ne teste que des adversaires que j'ai écrits ou repris d'ailleurs. La recherche automatique d'exploiteurs n'avait pas tourné depuis la phase 5b, contre la v3, et à l'époque elle trouvait à chaque fois un adversaire qui prenait 4 à 8 $ par manche au candidat. Cette phase la relance contre le nouveau bot de référence, sur le marché du site et à la table mixte de la règle d'entrée.

Résultat : la recherche ne trouve pas d'exploiteur. À 4 joueurs, le meilleur des 60 réglages finit 9,11 $ par manche derrière la v4c « achat ». À 5 joueurs, le meilleur fait jeu égal avec elle : -0,36 $ par manche, avec un intervalle qui contient 0. C'est un cousin de l'exploiteur lecteur, qui faisait déjà jeu égal en phase 5n. La promotion tient. Ces écarts sont mesurés contre des bots simulés, pas sur le site.

## Le changement

La recherche, `figgie/exploit.py`, date de la phase 4. Elle jouait sans la règle du site, et elle notait chaque réglage seul face à trois copies de la cible, c'est-à-dire avec le test de minorité, que la phase 5i a remplacé. Elle reçoit deux options :
- `--site` joue avec la règle du site : une nouvelle offre doit battre celle qui est affichée ;
- `--filler` note chaque réglage à la table mixte. Le score est alors l'écart entre le gain du réglage et celui de la cible, assis à la même table avec des Hard recalés, exactement comme dans la règle d'entrée.

J'ai aussi ajouté le lecteur du site aux sources de valeur possibles, à côté de l'heuristique, du bayésien et du marginal : sur le marché du site, un exploiteur qui lit les offres des autres avait une chance de faire mieux. Et la recherche affiche maintenant son avancement, étape par étape, avec le temps restant.

Un seul seam, écrit en TDD : avec un remplissant, le score d'un réglage est exactement `evaluate.mixed_gap` sur les mêmes donnes, à la règle du site. Le test vérifie aussi que, sur ces donnes, la règle du site change l'écart : sinon il ne pourrait pas voir une règle oubliée. Il échouait avant le code. J'ai ensuite vérifié qu'il attrape deux erreurs volontaires : oublier la règle du site, et garder l'ancien score à la place de la table mixte. Ce test vérifie ce que la recherche mesure, pas l'espace où elle cherche.

## La recherche

Les mêmes trois étapes qu'en phase 5b, chacune sur ses propres donnes pour ne pas garder un réglage simplement chanceux :
1. 60 réglages tirés au hasard, mesurés sur 20 donnes (graine 5) ;
2. les 6 meilleurs, remesurés sur 100 autres donnes (graine 6) ;
3. le meilleur des 6, mesuré sur les 300 donnes du tournoi (graine 1).

Parties de 10 manches, règle du site, Hard recalés comme remplissants, à 4 puis à 5 joueurs. Un réglage choisit sa source de valeur (heuristique, bayésien, marginal ou lecteur du site), son spread (1 à 12 $), sa marge (0 à 3 $), son temps de réaction (0,1 à 0,4 s), s'il cote ou se contente de prendre, et son rythme. Les 60 réglages tirés sont les mêmes aux deux tailles de table.

Écart réglage moins v4c « achat » à la table mixte, en dollars par manche. Un écart dont tout l'intervalle est au-dessus de 0 serait un exploiteur.

À 4 joueurs, étapes 2 et 3 :

| Réglage | étape 2 (100 donnes) | étape 3 (300 donnes) |
|---|---|---|
| **marginal, spread 4, marge 1, réaction 0,4 s, rythme 5 s** | **-8,50 [-10,28 ; -6,72]** | **-9,11 [-10,19 ; -8,04]** |
| lecteur du site, spread 8, marge 2, réaction 0,4 s, rythme 5 s | -11,55 [-12,79 ; -10,31] | |
| marginal, spread 6, marge 1, réaction 0,1 s, rythme 5 s | -11,61 [-13,42 ; -9,80] | |
| marginal, spread 3, marge 2, réaction 0,2 s, rythme 2 s | -12,04 [-13,73 ; -10,35] | |
| marginal, spread 8, marge 3, réaction 0,2 s, rythme 5 s | -12,78 [-14,34 ; -11,23] | |
| lecteur du site, spread 10, marge 3, réaction 0,3 s, rythme 2 s | -14,19 [-15,34 ; -13,04] | |

À 5 joueurs :

| Réglage | étape 2 (100 donnes) | étape 3 (300 donnes) |
|---|---|---|
| **marginal, spread 3, marge 2, réaction 0,2 s, rythme 2 s** | **+0,93 [-0,68 ; +2,54]** | **-0,36 [-1,27 ; +0,55]** |
| marginal, spread 4, marge 1, réaction 0,4 s, rythme 5 s | -2,26 [-3,98 ; -0,54] | |
| marginal, spread 3, marge 3, réaction 0,15 s | -3,13 [-4,78 ; -1,47] | |
| marginal, spread 6, marge 1, réaction 0,1 s, rythme 5 s | -5,25 [-7,01 ; -3,49] | |
| lecteur du site, spread 8, marge 2, réaction 0,4 s, rythme 5 s | -8,12 [-9,17 ; -7,07] | |
| marginal, spread 8, marge 3, réaction 0,2 s, rythme 5 s | -8,30 [-9,65 ; -6,94] | |

Tous les réglages complets, étape 1 comprise, sont dans `resultats/phase5o/`.

À 4 joueurs, aucun réglage ne s'approche de la v4c « achat ». Le meilleur finit 9 $ par manche derrière elle, à peu près comme l'exploiteur lecteur au tournoi complet de la phase 5n (-10,10 $).

À 5 joueurs, le meilleur réglage fait jeu égal. Il ressemble beaucoup à l'exploiteur lecteur de la phase 4 : la valeur du marginal, un spread serré, une réaction en 0,2 s et un rythme de 2 s (l'exploiteur lecteur cote avec un spread de 4 $ et une marge de 3 $). La recherche retrouve donc la seule faiblesse que le tournoi montrait déjà : à 5 joueurs, un marginal qui cote serré et vite tient tête à la v4c « achat ». Elle n'en trouve pas d'autre.

Le lecteur du site n'apporte rien. Son meilleur réglage finit à -11,55 $ à 4 joueurs et à -8,12 $ à 5. Lire les offres des autres ne l'aide pas face à ce bot.

## Le bot progresse-t-il ?

Cette phase n'a pas de nouveau candidat : elle teste le bot de référence. Il résiste mieux que ses prédécesseurs. En phase 5b, avec l'ancienne mesure, la recherche trouvait contre chaque candidat un adversaire qui lui prenait 4 à 8 $ par manche. Ici, le meilleur des 60 réglages perd 9 $ par manche à 4 joueurs et fait jeu égal à 5. Les deux mesures ne sont pas les mêmes, et je ne compare pas leurs chiffres directement. La promotion de la v4c « achat » tient : la règle prévue pour la retirer, un écart dont tout l'intervalle serait au-dessus de 0, n'est pas atteinte.

Ces écarts sont mesurés contre des bots simulés : ce ne sont pas des gains réels sur figgie.com.

## Limites

La recherche n'a essayé que 60 des 3 840 réglages possibles, tirés au hasard. Un réglage plus fort a pu lui échapper.

L'espace ne contient que des bots à valeur fixe, de la mécanique commune. Un exploiteur adaptatif, ou un bot qui fait autre chose que coter et prendre (se taire, mentir, regrouper ses cartes), n'y figure pas.

Les remplissants sont toujours des Hard recalés. Un exploiteur pourrait gagner à d'autres tables.

Le réglage à égalité à 5 joueurs n'entre pas dans les références de la table mixte : le plan ne prévoyait de l'ajouter que s'il battait la cible.

Depuis cette phase, l'espace contient le lecteur du site : les commandes de recherche des phases 4 et 5b tirent maintenant d'autres réglages. Pour retrouver leurs chiffres, il faut revenir à leur étiquette git.

Les durées ci-dessous excluent une hibernation du Mac de 2 h 34 pendant l'étape 3 à 4 joueurs. Elle a retardé la recherche sans en changer le résultat.

Tout reste mesuré contre des bots simulés. Ces gains ne sont pas des gains réels sur figgie.com.

## Reproduire

```bash
cd projets/bot-figgie
python3 -m unittest                                                  # les 145 tests, environ 7 s
python3 -m figgie.exploit --target v4c_achat --players 4 --rounds 10 --site --filler hard_simule_v2 \
    --candidates 60 --keep 6 --deals 20 100 300 --out recherche_4j.json
python3 -m figgie.exploit --target v4c_achat --players 5 --rounds 10 --site --filler hard_simule_v2 \
    --candidates 60 --keep 6 --deals 20 100 300 --out recherche_5j.json
```

Sur 10 cœurs, la recherche a pris environ 1 h 20 à 4 joueurs et 2 h 10 à 5 joueurs. Pour revenir exactement au code de cette phase : `git checkout phase5o-figgie`.
