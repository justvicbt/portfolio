# Phase 2 : ce que vaut vraiment une carte

*English version: [phase2.en.md](phase2.en.md)*

Jusqu'ici, le bot bayésien estimait une carte à « probabilité d'être l'objectif × 15 $ ». Les 15 $, c'était 10 $ de prime par carte plus un bonus fixe de 5 $ censé représenter la majorité du pot. Ce bonus était une approximation grossière. Une carte objectif peut ne rien changer à la majorité, ou au contraire la faire basculer et rapporter 100 $ d'un coup. Cette phase remplace le bonus par un vrai calcul, et donne naissance à un nouveau bot : le marginal.

Son premier objectif était de battre le passif, que personne n'avait réussi à battre en phases 0 et 1. Il y arrive, et il bat aussi tous les autres adversaires du zoo.

## La valeur d'une carte dépend de qui est en face

Prenons un exemple, avec 10 cartes objectif dans le paquet, donc 100 $ de reste du pot pour la majorité. J'ai 3 cartes objectif, un adversaire en a 3 aussi, les deux autres en ont 2. Nous partageons la majorité : je touche 30 $ plus la moitié des 100 $, soit 80 $.

Si j'achète une carte à l'autre meneur, je passe à 4 et lui à 2. Je suis seul en tête : 40 $ plus 100 $, soit 140 $. Cette carte me rapporte 60 $, six fois plus que la prime de 10 $.

Le joueur d'en face compte aussi. Si j'ai 4 cartes et que le meneur adverse en a 3, je touche 140 $. Si je vends une carte à un joueur qui n'en a qu'une, je descends à 3 et lui monte à 2 : je reste à égalité avec le meneur et je touche 80 $. Ça me coûte 60 $. Si je la vends au meneur, il passe à 4 et moi à 3 : il me prend la majorité, et je ne touche plus que 30 $. Ça me coûte 110 $. La même carte, au même instant, ne vaut pas la même chose selon l'acheteur.

C'est la relecture du code qui a repéré ce point. La première version du bot supposait que les autres ne bougeaient pas, alors que la carte qui change de main quitte forcément quelqu'un ou rejoint quelqu'un. J'ai corrigé avant le moindre tournoi.

## Monte Carlo : imaginer des milliers de tables possibles

Pour faire ce calcul, il faudrait connaître les mains des adversaires. On ne les connaît pas, mais on peut en imaginer. Le bot tire au hasard 300 versions possibles de la table, compatibles avec tout ce qu'il sait, calcule dans chacune ce que lui rapporte ou lui coûte une carte, puis fait la moyenne. C'est la méthode de Monte Carlo, du nom du casino : on remplace un calcul impossible par beaucoup de tirages.

Pour qu'une table imaginée soit compatible avec ce qu'il sait, trois choses doivent tenir :

- la composition du paquet (quelle couleur a 12 cartes, laquelle en a 8) est tirée selon sa probabilité, calculée à partir des cartes connues ;
- chaque adversaire a exactement son nombre de cartes, qui est public ;
- chaque adversaire a au moins les cartes qu'on lui connaît.

Ce dernier point, c'est le comptage des cartes. Chaque échange est public. Si un joueur achète deux cœurs, il en a au moins deux. S'il revend ensuite un cœur, il lui en reste au moins un. S'il vend un cœur alors qu'on ne lui en connaissait aucun, cette carte venait de sa donne, et on ne sait toujours rien. Ces minimums servent à la fois à tirer les tables et à affiner la probabilité de chaque couleur objectif : si un adversaire a acheté 4 trèfles, les trèfles sont probablement nombreux, et le pique, leur jumeau, devient plus probable comme objectif.

Le calcul se refait dès que la main du bot ou la liste des échanges change.

## Coter sans savoir qui prendra

Quand le bot prend la cotation d'un autre joueur, il sait qui est en face et utilise la valeur exacte pour ce joueur. Quand il affiche sa propre cotation, il ne sait pas qui viendra la prendre. Il reste alors prudent. Il propose d'acheter au prix que vaut une carte venant du pire vendeur possible, et de vendre au prix que coûte une carte partant chez le pire acheteur possible, en pratique celui qui pourrait lui prendre la majorité.

## Le réglage, sans tricher

Il reste deux paramètres : l'écart entre la valeur et la cotation affichée (le spread), et l'avantage minimal pour prendre une cotation (la marge). Les régler sur les donnes du tournoi reviendrait à choisir la combinaison qui a eu de la chance sur ces donnes-là. J'ai donc fait le réglage sur un autre jeu de donnes (graine 2, 150 donnes par adversaire), et le tournoi final sur les donnes habituelles (graine 1), que le réglage n'a jamais vues.

Le critère de choix est l'objectif du projet : la combinaison retenue est celle dont le pire résultat, contre tous les adversaires du zoo, est le meilleur. Pour le pire résultat, je prends la borne basse de l'intervalle de confiance, pas la moyenne. Les calculs tournent en parallèle sur les 10 cœurs du Mac, environ 4 minutes pour 15 combinaisons.

| Spread (marge 1 $) | 1 $ | 3 $ | 5 $ | 6 $ | 8 $ | 10 $ | 15 $ | 20 $ | 100 $ |
|---|---|---|---|---|---|---|---|---|---|
| Pire borne basse ($/manche) | +1,5 | +4,4 | +6,4 | +6,9 | +9,3 | +9,3 | +3,1 | +0,3 | 0,0 |
| Pire adversaire | passif | passif | passif | passif | passif | sniper | sniper | sniper | sniper |

Les marges de 0 $ et de 2 $ ont été testées pour chaque spread de 1 à 5 $, et 1 $ était toujours la meilleure ou presque. Les tableaux complets sont dans [`resultats/phase2/`](../resultats/phase2/).

Le meilleur réglage est loin de ce que j'imaginais au départ. Coter près de sa valeur, avec un spread de 1 ou 2 $, se fait exploiter par les adversaires rapides : le sniper prend les cotations dès qu'elles sont un peu mal placées. Ne jamais coter (100 $ de spread) ne rapporte rien face à ceux qui ne cotent pas non plus, comme le sniper : personne n'échange. Le sommet est entre les deux, vers 8 à 10 $. Le bot affiche des prix prudents et gagne surtout en prenant les erreurs des autres. J'ai retenu 8 $ : les deux réglages se valent, mais à 10 $ le pire adversaire devient le sniper, et c'est contre lui que le résultat chute dès qu'on élargit encore.

## Les tests

Les 50 tests se lancent en moins d'une seconde. Les nouveaux couvrent :

- le gain d'une carte, sur des cas calculés à la main : rompre une égalité, rattraper le meneur, vendre au meneur ou à un autre joueur, le cas des 8 cartes objectif ;
- le comptage des cartes, sur une suite d'échanges écrite à la main ;
- les tables tirées au hasard : elles respectent les nombres de cartes, les minimums connus et la composition du paquet ;
- la probabilité sans échange, qui retrouve la valeur de la phase 0 (60,9 % pour le trèfle avec 6 piques en main), et qui bouge dans le bon sens quand un adversaire révèle des cartes ;
- la version rapide du calcul, comparée à une version lente et lisible sur 4 000 tables.

Cette version rapide vient d'un profilage. Au départ, le bot marginal était 6 fois plus lent que les autres, et presque tout le temps partait dans la distribution des cartes inconnues. Or le calcul n'a besoin que d'une chose : combien de cartes objectif chaque adversaire reçoit. La version rapide ne place donc que ces 8 ou 10 cartes, au lieu de distribuer toute la table.

## Résultats

Même méthode que les phases précédentes : 1 000 donnes dupliquées par adversaire, sur la graine 1. Gain moyen en dollars par manche du bot en ligne face à des copies du bot en colonne.

### À 4 joueurs

| Candidat \ adversaires | aléatoire | heuristique | bayésien | agressif | passif | sniper | marginal |
|---|---|---|---|---|---|---|---|
| aléatoire | | -24,7 | -35,1 | +89,9 | -28,4 | -58,6 | -80,0 |
| heuristique | +16,1 | | -26,0 | +61,2 | -37,5 | -37,9 | -27,1 |
| bayésien | +53,5 | +33,5 | | +105,2 | -0,0 | +4,0 | +1,4 |
| agressif | -103,6 | -58,4 | -97,2 | | -96,4 | -116,6 | -81,0 |
| passif | +49,4 | +35,2 | -6,0 | +84,3 | | +0,7 | -6,6 |
| sniper | +105,5 | +73,1 | +0,4 | +178,4 | -0,0 | | -1,0 |
| marginal | +83,2 | +42,1 | +20,6 | +87,3 | +15,2 | +15,5 | |

### À 5 joueurs

| Candidat \ adversaires | aléatoire | heuristique | bayésien | agressif | passif | sniper | marginal |
|---|---|---|---|---|---|---|---|
| aléatoire | | -35,0 | -29,2 | +81,0 | -24,1 | -54,2 | -80,2 |
| heuristique | +26,1 | | -24,0 | +59,7 | -29,8 | -37,0 | -27,1 |
| bayésien | +49,2 | +31,3 | | +100,7 | -0,1 | +6,1 | +0,2 |
| agressif | -105,6 | -58,4 | -96,8 | | -99,7 | -118,4 | -86,8 |
| passif | +42,3 | +29,0 | -6,5 | +81,0 | | +0,1 | -4,2 |
| sniper | +95,9 | +79,2 | +0,4 | +183,0 | -0,1 | | -1,0 |
| marginal | +82,0 | +43,0 | +21,7 | +81,7 | +13,7 | +17,3 | |

Les cases des anciens bots entre eux sont identiques à la phase 1, au centime près. Leur code n'a pas changé, et les donnes sont les mêmes.

### La référence, phase 1 contre phase 2

| Contre | Bayésien, phase 1 (4 j.) | Marginal, phase 2 (4 j.) | Marginal, phase 2 (5 j.) |
|---|---|---|---|
| aléatoire | +53,5 | +83,2 [+81,4 ; +85,0] | +82,0 [+80,4 ; +83,7] |
| heuristique | +33,5 | +42,1 [+39,4 ; +44,9] | +43,0 [+40,8 ; +45,2] |
| bayésien | | +20,6 [+18,6 ; +22,6] | +21,7 [+19,5 ; +23,9] |
| agressif | +105,2 | +87,3 [+84,2 ; +90,4] | +81,7 [+79,4 ; +84,0] |
| passif | -0,05 | +15,2 [+14,0 ; +16,5] | +13,7 [+12,6 ; +14,9] |
| sniper | +4,0 | +15,5 [+14,3 ; +16,8] | +17,3 [+16,2 ; +18,4] |

Le bot s'améliore nettement. Le marginal passe la règle d'entrée, qui demande désormais de battre l'heuristique, le sniper et le bayésien. Il bat même le bayésien de +20,6 $ par manche. Il devient le nouveau bot de référence.

Pour la première fois, l'objectif du projet est atteint sur le zoo : un gain positif contre chaque adversaire, avec un intervalle de confiance qui exclut zéro, à 4 comme à 5 joueurs. Son pire adversaire est le passif, contre lequel il gagne +15,2 $ par manche à 4 joueurs, alors que le bayésien n'y gagnait rien.

Le seul recul est contre l'agressif (de +105,2 à +87,3 $). C'est le prix de la prudence : avec des cotations à 8 $ de sa valeur, le marginal laisse passer une partie des cartes que l'agressif surpaie.

## Ce que j'en retiens

Le marginal gagne surtout en prenant. Contre le passif, il ne fait que 2,3 échanges par manche, et il en tire 15 $. Il attend que le passif affiche une cotation mal placée pour lui, souvent parce qu'une carte précise lui ferait gagner la majorité, et il la prend. Le réglage le confirme : la combinaison gagnante cote loin et prend dès que l'avantage dépasse 1 $.

La position à la table compte. Seul face à trois bayésiens, le marginal gagne +20,6 $. Mais un bayésien seul face à trois marginaux gagne aussi un peu, +1,35 $, avec un intervalle [+0,34 ; +2,36] qui exclut zéro. Quand les marginaux sont en majorité, ils cotent tous loin et se disputent les mêmes erreurs, et un bayésien qui cote plus près en profite. La règle d'entrée ne teste qu'un candidat face à trois copies du même adversaire, donc elle ne voit pas ce cas. La ligue de la phase 4, où le bot jouera contre ses propres versions, devra le traiter.

Recalculer les valeurs après chaque échange ne relance pas le marché. Entre le marginal et trois heuristiques, les échanges s'arrêtent vers 17 secondes en médiane. Le bot recalcule ce que vaut une carte selon les cartes connues, mais il ne tire encore aucune conclusion de la façon dont les autres cotent. Un joueur qui propose 15 $ pour un trèfle en sait sans doute quelque chose. C'est le sujet de la phase 3.

La relecture du code a encore servi. Le défaut sur le joueur d'en face était un vrai trou de raisonnement, pas une faute de frappe, et le bot l'aurait payé en vendant des cartes au meneur.

## Limites

Tous les adversaires sont des bots que j'ai écrits. Le réglage a été fait sur d'autres donnes que le tournoi, mais contre les mêmes adversaires. Le bot est donc sans doute un peu adapté à ce zoo-là, et rien ne dit qu'un spread de 8 $ conviendrait contre des humains. La phase 4 entraînera des adversaires dont le seul but est de le battre, ce qui sera un test plus dur.

Le calcul de valeur garde deux simplifications. Quand un adversaire n'a aucune carte objectif dans une table imaginée, cette table est écartée pour l'achat, mais pour les autres couleurs le bot suppose que n'importe quel adversaire peut lui vendre. Et une cotation affichée révèle que son auteur a au moins une carte de cette couleur, ce que le comptage n'exploite pas encore.

Avec 300 tirages par calcul, la valeur obtenue varie d'un calcul à l'autre : son écart-type est de 0,85 $ en médiane et monte jusqu'à 2,5 $ dans les cas les plus incertains (mesuré sur 30 donnes). C'est assez pour un spread de 8 $, mais pas pour coter serré.

Les limites des phases précédentes tiennent toujours : temps de réaction inventés, quatre règles du site supposées, tables sans mélange de styles.

## Reproduire

```bash
cd projets/bot-figgie
python3 -m unittest                                         # les 50 tests, moins d'une seconde
python3 -m figgie.tune --deals 150                          # le réglage, environ 4 minutes sur 10 cœurs
python3 -m figgie.evaluate --candidate marginal --deals 1000 --seed 1
```

Le tournoi complet de la phase 2 (7 candidats, à 4 et à 5 joueurs) prend 34 minutes en lançant les 14 configurations en parallèle. Pour revenir exactement au code de cette phase : `git checkout phase2-figgie`.

## Et ensuite

La phase 3 apprend à lire le marché : déduire quelque chose des cotations et des échanges des autres, avec une vraisemblance apprise sur des parties simulées plutôt que fixée à la main. Elle repérera aussi, au fil de la partie, quels adversaires cotent selon leurs croyances et lesquels cotent au hasard.
