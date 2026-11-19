# Phase 1 : un simulateur plus fidèle

*English version: [phase1.en.md](phase1.en.md)*

La phase 0 jouait au Figgie au tour par tour : à chaque « tick », chaque bot agissait une fois, et le carnet ne gardait qu'une seule offre par couleur. Le vrai jeu ne ressemble pas à ça. Tout le monde agit en même temps, et le plus rapide prend la bonne affaire. Cette phase rapproche le simulateur de figgie.com, puis rejoue le tournoi pour voir si le classement tient.

Le bot de référence n'a pas changé. Cette phase ne cherche pas à l'améliorer : elle change le terrain sur lequel on le mesure.

## Ce que dit le site, et ce qu'il ne dit pas

J'ai relu la page des règles et la FAQ de figgie.com. Elles confirment l'essentiel : une carte par échange, toutes les cotations annulées après chaque échange, 350 $ au départ, un pot de 200 $. On achète en cliquant sur le bouton « buy » de n'importe quelle offre de vente, « pour le montant affiché ».

Quatre points restent flous, et je n'ai pas pu les trancher en jouant. J'ai donc fait un choix pour chacun, et le simulateur permet d'en changer.

| Question | Ce que dit le site | Choix du simulateur |
|---|---|---|
| Durée d'une manche | 4 minutes selon les règles, 2 minutes selon la FAQ | 4 minutes, réglable. J'ai testé les deux. |
| Combien de cotations par couleur | Le site parle de « n'importe quelle offre », sans préciser | Une offre d'achat et une offre de vente par joueur et par couleur |
| Nombre de cartes des adversaires et historique des échanges | Non précisé | Visibles, comme en phase 0 |
| Annuler sa cotation | Non précisé | Possible |

## Ce qui a changé dans le moteur

Le carnet garde maintenant une cotation par joueur. Chacun peut proposer d'acheter des cœurs à 5 $ pendant qu'un autre en propose 4 $ : les deux offres coexistent. Quand quelqu'un vend, il tombe sur la meilleure offre, et à prix égal sur la plus ancienne. C'est la règle « prix puis temps » des vraies bourses.

Le temps devient continu. Une manche dure 240 secondes. Chaque bot a deux réglages : son temps de réaction (le délai entre ce qu'il voit et l'arrivée de son action au marché) et la fréquence à laquelle il regarde le marché quand rien ne bouge. Dès que le marché change, tout le monde le voit, et la course commence. Si deux bots veulent la même carte affichée à 1 $, celui qui réagit en 0,1 seconde l'emporte sur celui qui réagit en 0,5 seconde. L'action du plus lent arrive sur un marché qui a déjà changé, et elle est refusée.

Ce réalisme a fait apparaître un problème, repéré pendant la relecture du code. Au départ, un ordre « acheter » partait sans prix. Un bot qui voyait une offre d'achat à 17 $ et décidait de vendre pouvait finir par vendre à 3 $, parce que le carnet avait bougé pendant que son ordre voyageait. Sur 2 592 prises mesurées, 11 se sont faites à un prix pire que celui vu par le bot. Sur figgie.com, on clique sur une cotation précise, donc ce cas ne peut pas arriver. Maintenant, chaque prise porte le prix que le bot a vu, et le marché la refuse si ce prix a empiré entre-temps. J'avais lancé un premier tournoi avant de m'en rendre compte. Je l'ai arrêté et relancé après la correction.

Le journal de chaque manche note aussi l'instant où le bot a regardé le marché, en plus de l'instant où son action est arrivée. L'écart entre les deux, c'est la latence. Elle servira quand le bot apprendra de ses parties. Le journal porte désormais un numéro de format, pour qu'un ancien journal de la phase 0 soit refusé avec un message clair au lieu d'une erreur obscure.

## Un nouvel adversaire : le sniper

La phase 0 avait une faiblesse : la règle d'entrée demandait seulement de battre l'heuristique, un adversaire assez facile. J'ai ajouté le sniper. Il a les mêmes estimations que le bayésien, mais il ne cote jamais. Il guette, et dès qu'une cotation est mal placée par rapport à sa valeur, il la prend. Avec 0,15 seconde de réaction, c'est le plus rapide du zoo.

Désormais, un candidat doit battre l'heuristique et le sniper, avec un intervalle de confiance entièrement au-dessus de zéro dans les deux cas.

Deux réglages des anciens adversaires ont aussi été revus. Le bot aléatoire se mettait à regarder le marché à chaque changement et s'emballait : plus de 1 000 actions par manche, au point de finir parfois avec 16 $. Il suit maintenant son propre rythme, calibré pour faire environ 67 actions par manche comme en phase 0. Le passif, lui, agit au plus une fois toutes les 5 secondes en moyenne, quelle que soit l'animation de la table.

## Les tests

Les 38 tests se lancent en moins d'une seconde. Les nouveaux vérifient en particulier :

- que deux joueurs peuvent avoir chacun leur offre dans la même couleur, et que la meilleure est servie en premier, puis la plus ancienne à prix égal ;
- qu'une prise est refusée si la cotation a empiré, et qu'elle se fait au prix affiché s'il est meilleur que prévu ;
- que le plus rapide gagne la course à une carte bradée, et que l'action du plus lent est refusée ;
- que toutes les actions tombent dans la durée de la manche, dans l'ordre ;
- qu'un bot du zoo n'est jamais refusé sans raison : à chaque refus, un autre joueur a agi entre le regard du bot et l'arrivée de son action.

## Résultats

Même méthode qu'en phase 0 : 1 000 donnes dupliquées par adversaire, gain moyen en dollars par manche du bot en ligne face à des copies du bot en colonne. Les intervalles de confiance sont dans [`resultats/phase1/`](../resultats/phase1/).

### À 4 joueurs

| Candidat \ adversaires | aléatoire | heuristique | bayésien | agressif | passif | sniper |
|---|---|---|---|---|---|---|
| aléatoire | | -24,7 | -35,1 | +89,9 | -28,4 | -58,6 |
| heuristique | +16,1 | | -26,0 | +61,2 | -37,5 | -37,9 |
| bayésien | +53,5 | +33,5 | | +105,2 | -0,0 | +4,0 |
| agressif | -103,6 | -58,4 | -97,2 | | -96,4 | -116,6 |
| passif | +49,4 | +35,2 | -6,0 | +84,3 | | +0,7 |
| sniper | +105,5 | +73,1 | +0,4 | +178,4 | -0,0 | |

### À 5 joueurs

| Candidat \ adversaires | aléatoire | heuristique | bayésien | agressif | passif | sniper |
|---|---|---|---|---|---|---|
| aléatoire | | -35,0 | -29,2 | +81,0 | -24,1 | -54,2 |
| heuristique | +26,1 | | -24,0 | +59,7 | -29,8 | -37,0 |
| bayésien | +49,2 | +31,3 | | +100,7 | -0,1 | +6,1 |
| agressif | -105,6 | -58,4 | -96,8 | | -99,7 | -118,4 |
| passif | +42,3 | +29,0 | -6,5 | +81,0 | | +0,1 |
| sniper | +95,9 | +79,2 | +0,4 | +183,0 | -0,1 | |

### Le bot de référence, phase 0 contre phase 1

| Bayésien contre | Phase 0, 4 joueurs | Phase 1, 4 joueurs | Phase 1, 5 joueurs |
|---|---|---|---|
| aléatoire | +120,7 | +53,5 | +49,2 |
| heuristique | +41,4 | +33,5 [+30,7 ; +36,3] | +31,3 [+29,2 ; +33,4] |
| agressif | +107,9 | +105,2 | +100,7 |
| passif | +0,0 | -0,05 [-0,20 ; +0,10] | -0,06 [-0,11 ; -0,01] |
| sniper | | +4,0 [+3,3 ; +4,6] | +6,1 [+5,5 ; +6,7] |

Le bayésien passe toujours la règle d'entrée, maintenant plus exigeante : il bat l'heuristique et le sniper, à 4 comme à 5 joueurs. Il reste le bot de référence.

Il ne s'est pas amélioré, et ce n'était pas le but de cette phase. Ses gains baissent contre l'aléatoire (de +120,7 à +53,5 $) parce que l'aléatoire ne peut plus acheter n'importe quoi à n'importe quel prix : ses prises portent un prix limite, souvent refusé. Ils baissent aussi un peu contre l'heuristique.

L'objectif final reste hors de portée, et le pire cas s'est même un peu dégradé. Contre le passif, le bayésien ne gagne toujours rien, et à 5 joueurs il perd 6 centimes par manche, avec un intervalle entièrement sous zéro. C'est minuscule, mais c'est la première fois qu'il perd nettement contre un adversaire du zoo.

Les manches de 2 minutes donnent les mêmes résultats que celles de 4, au centime près, sauf contre l'aléatoire (+36,5 $ au lieu de +53,5 $). L'explication est dans le constat suivant.

## Ce que j'en retiens

Le marché meurt au bout de 20 secondes. Entre le bayésien et trois heuristiques, la moitié des manches ont fini d'échanger après 21 secondes, sur une manche qui en dure 240. Face aux snipers, c'est 4 secondes. Ces bots calculent leur valeur une fois au début et ne la changent plus. Une fois que chacun a pris ce qui l'intéressait, plus rien ne bouge. Seul l'aléatoire maintient de l'activité jusqu'à la fin, ce qui explique pourquoi la durée de la manche ne compte que contre lui. Un vrai joueur, lui, continue d'apprendre en regardant les autres : un joueur qui achète beaucoup de trèfles en sait sans doute quelque chose. C'est le sujet de la phase 3, et c'est probablement là que se trouve le plus gros gain.

La vitesse a bouleversé le classement. Le sniper, qui ne cote jamais et ne fait que prendre, est devenu le deuxième meilleur bot : +73,1 $ contre l'heuristique, +178,4 $ contre l'agressif. L'agressif s'est effondré, de -35,6 à -103,6 $ contre l'aléatoire. Il réagit vite et paie jusqu'à 20 $ des cartes qui en valent rarement autant : en temps continu, il se jette sur chaque mauvaise affaire avant tout le monde. Le passif a fait le chemin inverse. Il bat maintenant l'heuristique de +35,2 $, contre +4,2 $ en phase 0, parce que l'heuristique et l'agressif viennent prendre ses cotations larges et lui paient sa prudence.

Le bayésien et le sniper se battent chacun un peu, selon qui est en minorité. Seul contre trois snipers, le bayésien gagne +4,0 $. Seul contre trois bayésiens, le sniper gagne +0,4 $. Ce n'est pas une contradiction : les deux tables ne sont pas les mêmes. Avec trois snipers, personne d'autre ne cote, donc les cotations du bayésien sont les seules du marché. Il fixe les prix, et c'est sans doute ce qui lui donne l'avantage.

Deux bugs ont été trouvés par la relecture avant d'arriver dans les résultats : les prises exécutées au mauvais prix, et le rythme de l'aléatoire, 18 % plus lent qu'annoncé. Un troisième venait de moi : le bot aléatoire qui s'emballait à 1 000 actions par manche, repéré parce qu'un gain de +350 $ par manche me paraissait trop beau. Comme en phase 0, un chiffre trop beau méritait d'être vérifié.

## Limites

Tous les adversaires sont toujours des bots que j'ai écrits. Ces chiffres ne disent rien du niveau face à des humains.

Les temps de réaction sont inventés : 0,15 seconde pour le sniper, 0,4 pour le bayésien, 1 seconde pour le passif. Je n'ai mesuré ni la latence réelle de figgie.com, ni la vitesse d'un joueur humain. Un humain met environ un quart de seconde à réagir à ce qu'il voit, puis doit cliquer. Le sniper est probablement plus rapide qu'un humain. Si le bot joue un jour sur le vrai site, sa vitesse devra rester humaine, sinon sa victoire tiendrait à ses réflexes et pas à son jeu.

Les quatre règles floues du site restent des hypothèses. Si figgie.com ne garde que la meilleure offre par couleur, ou cache le nombre de cartes des adversaires, certains résultats changeront.

Les tables ne mélangent toujours pas les styles : chaque match oppose le candidat à des copies d'un seul adversaire.

Le tournoi complet prend maintenant 39 minutes, contre 4 en phase 0, parce que chaque regard de chaque bot recopie le carnet. Ça suffit pour l'instant, mais il faudra accélérer le moteur avant l'apprentissage, qui demandera des centaines de milliers de manches.

## Reproduire

```bash
cd projets/bot-figgie
python3 -m unittest                                    # les 38 tests, moins d'une seconde
python3 -m figgie.evaluate --candidate bayesien --deals 1000 --seed 1
python3 -m figgie.evaluate --candidate bayesien --deals 1000 --seed 1 --duration 120   # manches de 2 minutes
```

Un candidat contre tout le zoo prend 2 à 4 minutes. Pour revenir exactement au code de cette phase : `git checkout phase1-figgie`.

## Et ensuite

La phase 2 remplace le bonus fixe du bayésien par un vrai calcul de ce que vaut une carte de plus : 10 $, plus ce qu'elle change à mes chances de gagner le reste du pot. Elle ajoute aussi le comptage des cartes et une exécution plus fine. Le premier objectif est de battre le passif, aujourd'hui son pire adversaire.
