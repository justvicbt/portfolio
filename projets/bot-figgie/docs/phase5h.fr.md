# Phase 5h : décrire la table sur plusieurs manches

*English version: [phase5h.en.md](phase5h.en.md)*

La phase 5g s'est terminée sur une piste. La v4c consulte ses voisins manche par manche, avec le profil d'une seule manche, et ce profil ne reconnaît pas la table de l'exploiteur. Faire d'abord la moyenne des profils des manches passées, puis consulter les voisins une seule fois, réduisait ce que l'exploiteur prend aux copies sur 100 donnes de diagnostic. Cette phase en fait une v4d et la passe au tournoi complet.

La v4d ne passe pas la règle d'entrée. L'exploiteur lui prend un peu moins qu'à la v4c, la v3 aussi, mais pas assez pour passer le test de minorité, et elle gagne un peu moins contre le marginal. Elle n'est pas promue, et la v4c reste mon meilleur bot.

## La v4d

La v4d ne change qu'une ligne de la v4c : la façon de choisir le réglage de la manche suivante. La v4c prend chaque profil passé, cherche ses 5 plus proches voisins parmi les tables d'entraînement, réunit tous ces voisins et choisit le réglage qui leur rapportait le plus. La v4d fait la moyenne des profils passés et cherche les 5 voisins de ce profil moyen. Elle tient compte de sa main comme la v4c, et elle reprend le modèle de la v4c tel quel, sans réentraînement.

Le test du seam vérifie, dans de vraies parties, qu'après une seule manche la v4d choisit exactement comme la v4c : la moyenne d'un seul profil, c'est ce profil. Pour m'assurer qu'il peut échouer, je l'ai faussé exprès en inversant la force de la main, et il a échoué. Il ne voit pas une erreur qui n'apparaîtrait qu'à partir de deux profils.

## Avant le tournoi : trois cases sur 300 donnes

La phase 5g avait mesuré la v4d sur 100 donnes de la graine 7. Je l'ai mesurée sur 200 donnes de plus, seulement sur les cases qui décident, en écarts appariés avec la v4c. Sur les 300 donnes :

| Écart v4d − v4c | 4 j. | 5 j. |
|---|---|---|
| exploiteur seul | **-0,62** [-0,89 ; -0,35] | **-0,59** [-0,81 ; -0,36] |
| v3 seule | -0,37 [-0,84 ; +0,11] | -0,45 [-0,96 ; +0,06] |
| marginal seul | +0,06 [-0,47 ; +0,59] | -0,11 [-0,63 ; +0,41] |
| contre le marginal | **-0,67** [-1,09 ; -0,26] | -0,23 [-0,61 ; +0,15] |

Les 200 donnes ajoutées vont dans le même sens que les 100 premières. Ce que l'exploiteur prend baisse d'environ 0,6 $ par manche, et c'est net. En échange, la v4d gagne environ 0,7 $ de moins contre le marginal à 4 joueurs. Si j'appliquais le seuil que je m'étais fixé pour la v4c calme en phase 5g, à savoir une borne basse au-dessus de -1 $ contre le marginal, elle échouerait de 9 centimes. Ce seuil servait à décider si une variante méritait un tournoi complet. Pour la v4d, le tournoi faisait de toute façon partie du plan de la phase.

## Les ordres refusés des références

La relecture du code de la phase 5g avait trouvé un défaut dans deux références. Avec la règle du site, une nouvelle offre doit battre celle qui est affichée. L'imitateur et les fondamentalistes tiraient leur prix sans en tenir compte. Environ la moitié de leurs ordres étaient refusés, et chaque refus leur faisait perdre leur tour.

Ils battent maintenant l'offre affichée d'1 $ quand leur prix tiré ne suffit pas, tant que ça reste dans leur valeur. Sinon, ils ne font rien. Trois tests le vérifient sur un carnet écrit à la main. Dans une partie de contrôle, il ne reste que 3 refus sur 215 ordres pour l'imitateur et 3 sur 147 pour le fondamentaliste, tous dus à la latence : le marché a bougé entre le moment où ils ont regardé et celui où leur ordre arrive.

Ces références sont donc un peu plus fortes, et leurs chiffres de la phase 5g ne sont plus comparables. J'ai rejoué la v4c contre elles sur les mêmes 300 donnes. Gain de la référence seule face aux copies, en dollars par manche :

| Référence seule face à la v4c | 4 j., phase 5g | 4 j., recalée | 5 j., phase 5g | 5 j., recalée |
|---|---|---|---|---|
| imitateur | -27,13 | -25,56 [-26,59 ; -24,53] | -24,24 | -20,37 [-21,46 ; -19,29] |
| fondamentaliste (r = 1,7) | -10,93 | -9,59 [-10,30 ; -8,88] | -6,88 | -5,47 [-6,12 ; -4,81] |
| fondamentaliste (r = 3,5) | -14,63 | -13,73 [-14,44 ; -13,03] | -11,23 | -10,89 [-11,42 ; -10,37] |

Elles perdent moins qu'avant, de 0,3 à 3,9 $ par manche, mais elles perdent toujours beaucoup. Aucune n'exploite la v4c.

## Le tournoi

Le tournoi est le même qu'en phase 5f : les mêmes 300 donnes (graine 1), la règle du site, des parties de 10 manches. J'ai ajouté la v4c aux adversaires, et toutes les références de la phase 5g. La v4c n'a pas changé depuis la phase 5f, et le moteur est déterministe, donc je compare la v4d aux chiffres de la v4c de la phase 5f.

Au test de minorité, chaque chiffre est le gain de la référence seule face aux copies : plus il est bas, mieux mes copies se défendent.

| | v4c, 4 j. | v4d, 4 j. | v4c, 5 j. | v4d, 5 j. |
|---|---|---|---|---|
| contre le marginal | +7,75 | +7,05 [+6,55 ; +7,54] | +4,59 | +4,39 [+3,93 ; +4,86] |
| contre la v3 | -1,03 | -1,09 [-1,55 ; -0,62] | -0,02 | +0,12 [-0,30 ; +0,53] |
| contre la v4b | +0,13 | -0,02 [-0,35 ; +0,31] | -0,09 | -0,19 [-0,52 ; +0,14] |
| contre la v4c | | -0,12 [-0,44 ; +0,20] | | -0,12 [-0,42 ; +0,18] |
| exploiteur seul | +3,15 | **+2,77** [+2,31 ; +3,23] | +4,65 | **+4,42** [+4,05 ; +4,78] |
| v3 seule | +0,94 | **+0,60** [+0,11 ; +1,09] | +2,46 | **+2,00** [+1,44 ; +2,55] |
| v4b seule | +0,16 | **+0,49** [+0,18 ; +0,81] | +0,32 | **+0,46** [+0,13 ; +0,79] |
| v4c seule | | +0,17 [-0,15 ; +0,48] | | +0,23 [-0,08 ; +0,54] |
| marginal seul | -0,80 | -0,76 [-1,28 ; -0,24] | +0,77 | +0,22 [-0,32 ; +0,75] |

En gras, les références qui gagnent de l'argent face aux copies de la v4d : la règle d'entrée échoue à 4 et à 5 joueurs, à cause du test de minorité. Sans ce test, elle passerait, comme la v4c.

Contre les autres bots du zoo, la v4d fait à peu près comme la v4c : à moins de 1 $ par manche près contre le Hard simulé, l'heuristique, le sniper et le bayésien. Les six références trouvées en phase 5g perdent toutes face à ses copies, de 3 à 26 $ par manche.

Comparée à la v4c, la v4d a un bilan mitigé. L'exploiteur lui prend 0,38 $ de moins à 4 joueurs et 0,23 $ de moins à 5, la v3 0,34 et 0,46 $ de moins, le marginal seul 0,55 $ de moins à 5 joueurs. Mais la v4b lui prend un peu plus, de 0,14 à 0,33 $, et elle gagne 0,70 $ de moins contre le marginal à 4 joueurs. Face à face, aucune des deux ne bat l'autre : tous les intervalles touchent 0.

Il faut lire ces écarts avec prudence. Le tournoi ne garde que les moyennes, pas les valeurs donne par donne, donc je ne peux pas calculer les écarts appariés. Les intervalles affichés sont ceux de chaque bot, et ceux de la v4c et de la v4d se recouvrent dans toutes les cases. C'est sur la graine 7 que l'effet sur l'exploiteur est net, en écarts appariés.

Le bot ne progresse donc pas nettement. Aucun bot n'est promu, et la v4c reste le meilleur. Tous ces chiffres sont mesurés contre des bots simulés : ce ne sont pas des gains réels.

## Ce que j'en retiens

Regarder plusieurs manches à la fois aide un peu les copies à reconnaître la table de l'exploiteur, mais seulement un peu : il leur prend encore 2,77 $ et 4,42 $ par manche. Le diagnostic de la phase 5g disait que leurs voisins venaient d'une vingtaine de tables d'entraînement différentes. Moyenner les profils réduit le bruit d'une manche, mais ne crée pas de table d'entraînement qui ressemble à celle de l'exploiteur.

Pour le coût contre le marginal, j'ai une hypothèse que je n'ai pas vérifiée : un profil moyen change lentement, donc la v4d réagirait moins vite que la v4c quand la table change de comportement d'une manche à l'autre.

## Et ensuite

Ces deux phases ont essayé d'améliorer la façon dont les copies choisissent leur réglage, et l'exploiteur garde à peu près les mêmes gains. Je pense qu'il faut maintenant changer de levier, la seconde piste de la phase 5f : la façon de vendre les cartes objectif, ou de disputer la majorité. L'exploiteur gagne en vendant aux copies, et aucun réglage de spread ou de marge ne l'en empêche. Une autre idée serait d'ajouter aux tables d'entraînement des tables avec un exploiteur, pour que les voisins le reconnaissent. Je proposerai un plan avant de commencer.

## Limites

Le tournoi ne garde pas les valeurs donne par donne : la comparaison entre la v4c et la v4d n'est pas appariée, et ses intervalles se recouvrent. Le diagnostic apparié porte sur 300 donnes d'une autre graine, et seulement sur quatre cases.

La v4d reprend le modèle de la v4c, appris sur des profils d'une seule manche, et le consulte avec un profil moyen, plus régulier qu'un profil d'une manche. Un modèle appris sur des profils moyens irait peut-être mieux, mais il faudrait le réentraîner.

Les références recalées ne sont plus celles de la phase 5g. Leurs nouveaux chiffres valent pour les deux versions de la v4, mais pas pour les tableaux de la phase 5g.

Tout reste mesuré contre des bots simulés. Ces gains ne sont pas des gains réels sur figgie.com.

## Reproduire

```bash
cd projets/bot-figgie
python3 -m unittest                                                  # les 128 tests, environ 5 s
python3 -m figgie.tournoi --site --candidates adaptatif_v4d --rounds 10 --deals 300 --no-tables \
    --opponents hard_simule heuristique sniper bayesien marginal adaptatif_v3 adaptatif_v4b adaptatif_v4c \
    --references hard_simule heuristique sniper bayesien marginal adaptatif_v3 adaptatif_v4b adaptatif_v4c \
        exploiteur exploiteur_lecteur imitateur fondamentaliste fondamentaliste_35 vendeur mante parieur \
    --out tournoi_site.json
python3 -m figgie.tournoi --site --candidates adaptatif_v4c --rounds 10 --deals 300 --no-tables \
    --opponents inactif --references imitateur fondamentaliste fondamentaliste_35 --out tournoi_v4c_references.json
```

Le premier tournoi prend 3 h 30 sur 10 cœurs, le second 1 h 15. Pour revenir exactement au code de cette phase : `git checkout phase5h-figgie`.
