# Phase 5m : trois défauts corrigés, et un nouveau point de départ

*English version: [phase5m.en.md](phase5m.en.md)*

La relecture complète du code, après la phase 5l, a trouvé trois défauts qui changent le jeu des bots. Ce sont des erreurs dans ce que j'avais déjà écrit. Je les corrige avant de continuer, parce que les phases suivantes se compareraient sinon à des chiffres faux. Le prix à payer : plus aucun chiffre d'avant ne se compare directement à ceux de cette phase.

Au tournoi, sur les mêmes donnes que la phase 5l, la v4c au temps passe toujours la règle d'entrée à 4 joueurs et reste refusée à 5. Une seule référence la refuse maintenant : la v4c qui se tait la première minute, qui fait 3,05 $ de mieux qu'elle par manche à la table mixte (2,46 $ en phase 5l). L'exploiteur lecteur ne la refuse plus : son écart, +0,22 $, a un intervalle qui contient 0. Aucun bot n'est promu.

## Retirer un seul côté

Sous la règle du site, une offre ne peut que s'améliorer : pour baisser mon offre d'achat, je dois d'abord la retirer. Mes bots le faisaient avec la seule action de retrait du moteur, qui retirait mes deux cotations de la couleur. Quand un bot voulait seulement baisser son offre d'achat, il perdait aussi son offre de vente, et devait la reposer au tour suivant, s'il le pouvait encore : entre-temps, quelqu'un d'autre pouvait avoir pris la place.

Le site, lui, distingue les deux retraits : les journaux de Rasmus contiennent des retraits d'offre d'achat (`xb`) et d'offre de vente (`xo`). Le moteur accepte maintenant `("cancel", couleur, "bid")` et `("cancel", couleur, "ask")`, et le fil public dit quel côté a disparu. L'ancienne forme, sans côté, retire toujours les deux.

Les seams, écrits en TDD :
- dans le moteur, retirer mon offre d'achat laisse mon offre de vente, et le fil public le dit. Le test échoue si le retrait d'un côté retire les deux ;
- un bot qui veut baisser son offre d'achat sous la règle du site retire seulement celle-ci. Le test échouait avant la correction : le bot renvoyait le retrait des deux côtés.

Je n'ai pas touché au Hard recalé de la phase 5j : il retire toujours ses deux cotations, et il a été recalé sur les vraies manches avec ce comportement.

## La valeur d'achat du marginal

Quand un joueur me vend une carte, il prouve qu'il en avait une. Le Monte Carlo du marginal en tient compte : il retire les mondes où ce joueur n'avait aucune carte de la couleur. Mais il ne le faisait que pour les mondes où la couleur est l'objectif, parce qu'il ne place que les cartes objectif. Les mondes où la couleur n'est pas l'objectif restaient tous comptés, même ceux où le vendeur ne pouvait pas avoir la carte. Comme la carte y vaut 0 $, ils tiraient la valeur d'achat vers le bas.

Pour ces mondes, je n'ai pas besoin de placer les cartes : je calcule directement la probabilité que le vendeur ait au moins une carte de la couleur, d'après le nombre de places qu'il lui reste (une loi hypergéométrique). Chaque monde compte avec ce poids.

L'écart est faible en général, mais il devient grand face à un joueur dont on connaît presque toute la main. Le seam compare la valeur rapide à une moyenne faite à la main sur des tables entières tirées au hasard, comme le test le faisait déjà. Sa référence reproduisait le même défaut, et je l'ai corrigée. Je l'ai aussi fait porter sur un joueur qui n'a plus qu'une place inconnue : l'ancienne valeur rapide donnait 1,84 $ à une carte de pique achetée chez lui, la référence environ 5,80 $. Le test échoue sur l'ancien code et passe sur le nouveau.

Cette correction change le jeu du marginal et de tous les bots qui en héritent. Le test de référence du moteur, qui rejoue des manches fixées, change donc aussi. Je l'ai régénéré sur les mêmes tables et les mêmes graines : la seule table sans bot à valeur marginale (bayésien, passif, sniper, agressif, heuristique) donne exactement les mêmes résultats qu'avant, ce qui confirme que le moteur, lui, n'a pas bougé.

## Le profil de table

Les bots adaptatifs décrivent la table par quelques nombres, dont l'écart entre les prix d'achat et de vente de chaque adversaire. Sous la règle du site, une nouvelle offre efface celle qui était affichée. Le profil ne le savait pas : il gardait l'offre effacée, et pouvait l'apparier plus tard avec une vente du même joueur, pour un écart que ce joueur n'avait jamais affiché.

Le profil suit maintenant la règle du site quand la manche la suit, et les retraits d'un seul côté. Deux seams, sur des fils écrits à la main : une offre battue ne compte plus dans l'écart (le test échoue si j'enlève la règle), et un retrait d'achat laisse l'offre de vente s'apparier avec la nouvelle offre d'achat.

Les plus proches voisins de la v4c ont appris sur ces profils. Changer le profil en jeu sans réentraîner leur aurait montré des profils qu'ils n'ont jamais vus. J'ai donc réappris la v4c et la v4c au temps de la phase 5l sur leurs 188 tables, avec le code corrigé. Les anciennes versions (v3, v4, v4b) gardent leurs modèles : elles jouent avec le profil corrigé, sur des voisins appris avec l'ancien.

## Le réentraînement

Avec le code corrigé, la v4c a mis 156 minutes à réapprendre ses 188 tables. Sa validation croisée a presque la même valeur qu'à la phase 5f : le réglage qu'elle choisit gagne +2,61 $ par manche de plus que le réglage fixe [+2,08 ; +3,13], contre +2,48 $ [+1,91 ; +3,05] avec l'ancien code. Ses voisins apprennent donc aussi bien sur le profil corrigé.

La v4c au temps de la phase 5l, réapprise de la même façon, a mis 332 minutes. Le réglage choisi gagne +4,23 $ par manche de plus que le réglage fixe [+3,67 ; +4,78], contre +3,76 $ [+3,24 ; +4,27] à la phase 5l. Les deux intervalles se recouvrent en grande partie : je ne conclus pas à un progrès, seulement que l'apprentissage n'a pas souffert de la correction.

## Le tournoi

Même format qu'en phase 5l : graine 1, 100 donnes de 10 manches, les mêmes 12 références à la table mixte, avec le Hard recalé comme remplissant. Les donnes sont les mêmes, mais la plupart des bots ont changé avec les corrections, pas seulement le candidat :
- le retrait d'un seul côté change le jeu de tous les bots à valeur fixe sous la règle du site (heuristique, sniper, bayésien, exploiteur) ;
- la valeur d'achat et le profil changent le marginal et toutes les versions adaptatives, et la v4c, la v4c qui se tait et la v4c vendeuse jouent avec le modèle réappris.

Seuls les deux Hard simulés, le vendeur et le parieur jouent exactement comme en phase 5l. Pour eux, l'écart entre les deux phases ne vient que du candidat. Pour les autres, je compare des chiffres, pas un même adversaire.

Face à trois copies d'un même adversaire (gain du candidat, en dollars par manche) :

| Adversaire | 5m, 4 j. | 5m, 5 j. | 5l, 4 j. | 5l, 5 j. |
|---|---|---|---|---|
| heuristique | +42,48 [+40,07 ; +44,89] | +37,54 [+35,67 ; +39,40] | +42,09 | +36,78 |
| sniper | +33,81 [+32,47 ; +35,15] | +31,51 [+30,28 ; +32,75] | +30,85 | +27,50 |
| bayésien | +24,31 [+22,43 ; +26,18] | +23,41 [+21,91 ; +24,90] | +23,68 | +22,20 |
| marginal | +12,19 [+11,18 ; +13,19] | +12,40 [+11,46 ; +13,34] | +9,74 | +8,04 |
| Hard de la phase 5c (inchangé) | +38,24 [+36,80 ; +39,67] | +34,40 [+33,04 ; +35,77] | +37,40 | +31,86 |
| Hard recalé (inchangé) | +15,26 [+13,49 ; +17,04] | +13,13 [+11,62 ; +14,63] | +15,18 | +12,78 |

À la table mixte (écart référence moins candidat, en dollars par manche ; un écart dont tout l'intervalle est au-dessus de 0 refuse le candidat) :

| Référence | 5m, 4 j. | 5m, 5 j. | 5l, 4 j. | 5l, 5 j. |
|---|---|---|---|---|
| Hard recalé (inchangé) | -20,61 [-22,98 ; -18,23] | -16,28 [-18,23 ; -14,33] | -19,96 | -16,36 |
| bayésien | -21,94 [-23,70 ; -20,19] | -18,97 [-20,29 ; -17,64] | -24,55 | -20,14 |
| marginal | -14,67 [-16,28 ; -13,05] | -10,54 [-12,24 ; -8,84] | -15,13 | -11,80 |
| v3 | -9,96 [-11,88 ; -8,03] | -6,30 [-7,74 ; -4,86] | -10,65 | -8,66 |
| v4b | -8,36 [-9,94 ; -6,79] | -1,68 [-3,12 ; -0,24] | -7,64 | -1,79 |
| v4c | -8,08 [-9,43 ; -6,73] | -2,64 [-3,98 ; -1,29] | -7,27 | -1,74 |
| v4c calme 60 s | -1,09 [-2,24 ; +0,06] | **+3,05 [+1,97 ; +4,13]** | -1,33 | **+2,46** |
| v4c vendeuse (5k) | -3,07 [-4,22 ; -1,92] | +0,02 [-0,83 ; +0,87] | -3,49 | +0,45 |
| exploiteur | -17,24 [-18,89 ; -15,59] | -15,90 [-17,13 ; -14,66] | -17,50 | -14,69 |
| exploiteur lecteur | -6,64 [-8,56 ; -4,71] | +0,22 [-1,07 ; +1,51] | -6,97 | **+1,66** |
| vendeur (inchangé) | -15,42 [-16,67 ; -14,17] | -10,25 [-11,32 ; -9,18] | -14,35 | -9,55 |
| parieur (inchangé) | -13,02 [-15,13 ; -10,92] | -12,77 [-14,23 ; -11,30] | -13,53 | -12,82 |

À 4 joueurs, la v4c au temps passe comme en phase 5l. Son écart le plus proche de 0, -1,09 $ face à la v4c qui se tait, a maintenant un intervalle qui dépasse 0 de 6 centimes. La règle ne refuse que les écarts dont tout l'intervalle est au-dessus de 0, donc elle passe, mais de moins loin qu'en phase 5l.

À 5 joueurs, il ne reste qu'un refus. L'exploiteur lecteur passe de +1,66 $ à +0,22 $, avec un intervalle qui contient 0. La v4c qui se tait, elle, passe de +2,46 $ à +3,05 $. Les deux intervalles de la v4c qui se tait se recouvrent largement : je ne peux pas dire que l'écart a grandi, seulement qu'il ne s'est pas refermé.

Face au zoo, les chiffres montent un peu partout, surtout face au marginal (+12,19 $ et +12,40 $ par manche, contre +9,74 $ et +8,04 $). Mais le marginal a lui-même changé : sa valeur d'achat est corrigée, et je ne sais pas si cette hausse vient du candidat ou de son adversaire. Face aux deux Hard simulés, qui n'ont pas changé, le gain est stable à 4 joueurs et monte à 5 joueurs, de +31,86 $ à +34,40 $ face au Hard de la phase 5c. Les deux tournois ne sont pas appariés entre eux : ce sont deux mesures séparées sur les mêmes donnes.

## Le bot progresse-t-il ?

Pas au sens de la règle d'entrée : la v4c au temps est toujours refusée à 5 joueurs, et le marginal reste le bot de référence. Elle n'a plus qu'une référence contre elle au lieu de deux, mais son pire écart est un peu plus grand. Cette phase corrige des erreurs et donne un point de départ juste à la phase 5n, qui gardera le poids de la majorité à l'achat seulement. C'est là que se joue le refus de la v4c qui se tait, puisque le diagnostic de la phase 5l montrait que le bot lui cède ses cartes objectif trop tôt.

Ces gains sont mesurés contre des bots simulés : ce ne sont pas des gains réels sur figgie.com.

## Limites

Le Hard recalé de la phase 5j retire toujours ses deux cotations d'une couleur à la fois. Je ne l'ai pas changé, parce qu'il a été réglé sur les vraies manches avec ce comportement. Mais le site permet de retirer un seul côté, et le Hard est notre remplissant de la table mixte.

Les modèles de la v3, de la v4 et de la v4b n'ont pas été réappris. Ils jouent avec le profil corrigé, sur des voisins appris avec l'ancien.

Presque tous les bots ont changé entre la 5l et la 5m. La comparaison entre les deux phases mêle donc l'effet des corrections sur le candidat et sur ses adversaires.

Le tournoi est réduit comme ceux des phases 5j à 5l : 100 donnes au lieu de 300, et une partie des références.

Tout reste mesuré contre des bots simulés. Ces gains ne sont pas des gains réels sur figgie.com.

## Reproduire

```bash
cd projets/bot-figgie
python3 -m unittest                                                  # les 142 tests, environ 7 s
python3 -m figgie.adapt --v4t sans --deals 40 --rounds 3 \
    --arms 6,3,6,3 8,1,8,1 10,3,10,3 12,3,12,3 8,1,3,1 12,3,4,1 --report entrainement_v4c.json
python3 -m figgie.adapt --v4t 120,0.5 --deals 40 --rounds 3 \
    --arms 6,3,6,3 8,1,8,1 10,3,10,3 12,3,12,3 8,1,3,1 12,3,4,1 --report entrainement_v4t.json
python3 -m figgie.tournoi --site --candidates v4c_temps --rounds 10 --deals 100 --no-tables \
    --opponents heuristique sniper bayesien marginal hard_simule hard_simule_v2 --references \
    --mixed hard_simule_v2 bayesien marginal adaptatif_v3 adaptatif_v4b adaptatif_v4c v4c_calme_60 v4c_vente_60 \
        exploiteur exploiteur_lecteur vendeur parieur --out tournoi.json
```

Sur 10 cœurs, le réentraînement de la v4c a pris 2 h 36 et réécrit `modeles/adaptation_v4c.json`. Celui de la v4c au temps a pris 5 h 32 et réécrit `modeles/adaptation_v4t.json`. Le tournoi a pris 2 h 11. Pour revenir exactement au code de cette phase : `git checkout phase5m-figgie`.
