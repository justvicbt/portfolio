# Phase 3 : lire le marché

*English version: [phase3.en.md](phase3.en.md)*

Jusqu'ici, le bot ne tirait ses conclusions que de deux sources : sa propre main, et les cartes que les échanges révèlent chez les autres. Il ignorait tout le reste, en particulier la façon dont les autres cotent. Or un joueur qui propose 12 $ pour un cœur en sait sans doute quelque chose. Cette phase apprend à lire ces signaux, sur des parties simulées, et donne naissance à un nouveau bot, le lecteur.

Elle ajoute aussi des parties de plusieurs manches à la même table, comme sur figgie.com. À la fin de chaque manche, la couleur objectif et les mains de tous sont révélées, et le bot peut apprendre à qui se fier. C'est la première forme d'apprentissage d'une partie à l'autre.

Le bilan est contrasté, et je le donne tel quel. Le bot devine beaucoup mieux la couleur objectif, mais ça rapporte peu de dollars, et le lecteur ne passe pas la règle d'entrée à 5 joueurs. Il n'est donc pas promu : le marginal de la phase 2 reste le bot de référence.

## Ce qu'on voit à l'écran

Sur figgie.com, chaque joueur voit passer les cotations et les échanges. Le simulateur tient désormais ce même fil public : chaque offre d'achat ou de vente affichée, chaque carte qui change de main, avec son prix et le joueur concerné. Les bots le lisent directement dans leur vue.

Une première version faisait reconstruire ce fil par le bot lui-même, en comparant ce qu'il voyait d'un regard à l'autre. La relecture du code a montré le défaut : pendant que l'action du bot était en route, il ne regardait pas, et il ratait des cotations. Or le modèle avait appris sur toutes les cotations. Un vrai joueur, lui, continue de voir l'écran après avoir cliqué. Le fil tenu par le marché règle le problème, et un test vérifie qu'à chaque regard, le bot voit exactement le début du fil reconstruit à partir du journal.

## Apprendre ce que dit une cotation

La méthode est volontairement simple, sans bibliothèque d'apprentissage : on compte.

On joue 4 000 manches à des tables mixtes, tirées au hasard dans le zoo, à 4 ou 5 joueurs. Chaque événement du fil est rangé par type, c'est-à-dire sa nature (offre d'achat, offre de vente, achat, vente) et sa tranche de prix (1-2 $, 3-5 $, 6-9 $, 10-14 $, 15 $ et plus). On compte ensuite combien de fois chaque type apparaît, par manche, dans la couleur objectif, dans sa jumelle et dans les deux autres couleurs. Le rapport entre ces fréquences dit à quel point un type d'événement trahit la couleur objectif.

Pendant une manche, le bot multiplie ces rapports pour chaque événement qu'il voit, et en tire une probabilité pour chaque couleur. Les tests vérifient le calcul sur un petit jeu de données écrit à la main, avec un résultat connu à l'avance (10/14 pour le cœur après une offre à 12 $).

Les manches d'apprentissage utilisent leurs propres graines (3), les mesures de validation d'autres graines (4). Aucune ne sert aux tournois (graine 1) ni au réglage de la phase 2 (graine 2).

## Trois pièges, trouvés en mesurant

Mon ancien code avait déjà buté sur ce problème : avec les cotations adverses, la précision tombait de 39 % à 14 %, parce que les signaux noyaient tout. J'ai retrouvé exactement ce phénomène, et trois causes.

Premier piège, les répétitions. Un joueur qui reposte dix fois la même offre n'en sait pas dix fois plus, mais un modèle naïf compte dix preuves. Sans précaution, les probabilités devenaient bien trop tranchées. Désormais, chaque signal ne compte qu'une fois par joueur et par manche (même nature, même couleur, même tranche de prix).

Deuxième piège, le double comptage. Un échange révèle des cartes, et le comptage des cartes de la phase 2 en tient déjà compte. Si le modèle relit aussi « il a acheté un trèfle », il compte deux fois la même information. La relecture du code l'a signalé. J'ai mesuré les deux versions sur les manches de validation : ne lire que les cotations, et laisser les échanges au comptage, donne de meilleures probabilités.

Troisième piège, le plus inattendu. En vérifiant la calibration, j'ai trouvé un défaut présent depuis la phase 2. Le comptage traitait les cartes achetées par les autres comme si elles avaient été tirées au hasard dans le paquet. Or un joueur qui achète 6 cœurs les a choisis : ça ne prouve pas que le cœur est la couleur de 12. Seule ma donne de départ est un vrai tirage au hasard. Les cartes connues des autres ne doivent servir qu'à exclure les paquets impossibles : une couleur ne peut pas avoir moins de cartes qu'on n'en connaît. Avec l'ancienne méthode, quand le bot annonçait 80 à 90 %, il n'avait raison que 42 % du temps. Le bot marginal de la phase 2 garde ce défaut, pour rester une référence mesurée. Le lecteur utilise la version corrigée.

## Ce que ça change pour deviner l'objectif

Mesure sur 1 000 manches de validation, du point de vue d'un joueur qui ne voit que sa main et le fil public. Pourcentage de manches où la couleur jugée la plus probable est la bonne.

| Ce que le bot utilise | 5 s | 15 s | 30 s | 60 s | 120 s | 240 s |
|---|---|---|---|---|---|---|
| Sa main seule | 38-40 % | | | | | |
| Comptage de la phase 2 | | | | 42 % | | |
| Comptage corrigé | 39,4 % | 43,1 % | 44,9 % | 47,2 % | 48,3 % | 49,6 % |
| Comptage corrigé + cotations | 49,2 % | 51,6 % | 51,3 % | 52,4 % | 55,1 % | 56,8 % |

Au hasard, on aurait 25 %. La lecture des cotations apporte l'essentiel dans les 5 premières secondes : c'est le moment où chacun affiche ses premiers prix, qui reflètent sa main.

Les probabilités sont aussi devenues honnêtes. À 60 secondes, quand le lecteur annonce 20 à 30 %, la couleur est l'objectif 26 % du temps. À 50-60 %, c'est 59 %. À 70-80 %, 84 %. Le modèle retenu ne lit que les cotations, sans atténuation : une fois les répétitions et le double comptage retirés, il n'y avait plus d'excès de confiance à corriger.

## Les parties de plusieurs manches

Le moteur sait maintenant jouer une partie de N manches à la même table. Chaque bot a une mémoire qui survit d'une manche à l'autre. À la fin de chaque manche, il apprend la couleur objectif et voit les mains de tous, comme sur le site. Les donnes dupliquées fonctionnent toujours : c'est la partie entière qui est rejouée à chaque rotation des sièges. La première manche d'une partie utilise la même donne qu'une manche isolée de même graine. Les suivantes ont des graines qui ne peuvent croiser aucune graine des autres expériences.

Le lecteur s'en sert pour juger ses adversaires. À la fin d'une manche, il regarde si les signaux de chacun pointaient vers la vraie couleur objectif, mieux que le hasard. Un joueur qui cote au hasard voit sa confiance baisser, un joueur fiable la voit monter. Sur des joueurs synthétiques, après 20 manches, un joueur fiable reçoit un poids de 1,33 et un joueur aléatoire de 0,18.

## Les tests

Les 74 tests se lancent en une seconde. Les nouveaux couvrent :

- le fil d'événements, qui doit être identique en direct et reconstruit depuis le journal ;
- le modèle de signaux : rapports calculés à la main, une cotation répétée qui ne compte qu'une fois, mes propres événements ignorés, la lecture limitée aux cotations ;
- le comptage corrigé : des cartes achetées qui excluent les paquets impossibles sans peser comme un tirage ;
- les parties de plusieurs manches : mémoire, révélation des mains, argent conservé, bot contre lui-même toujours à zéro ;
- le modèle d'adversaire, sur des joueurs synthétiques.

## Résultats

Même méthode que les phases précédentes : 1 000 donnes dupliquées par adversaire, sur la graine 1, manches isolées. Gain moyen en dollars par manche du bot en ligne face à des copies du bot en colonne. Le tournoi complet a pris 1 h 52 sur 10 cœurs.

### À 4 joueurs

| Candidat \ adversaires | aléatoire | heuristique | bayésien | agressif | passif | sniper | marginal | lecteur |
|---|---|---|---|---|---|---|---|---|
| aléatoire | | -24,7 | -35,1 | +89,9 | -28,4 | -58,6 | -80,0 | -67,8 |
| heuristique | +16,1 | | -26,0 | +61,2 | -37,5 | -37,9 | -27,1 | -22,4 |
| bayésien | +53,5 | +33,5 | | +105,2 | -0,0 | +4,0 | +1,4 | -0,9 |
| agressif | -103,6 | -58,4 | -97,2 | | -96,4 | -116,6 | -81,0 | -66,4 |
| passif | +49,4 | +35,2 | -6,0 | +84,3 | | +0,7 | -6,6 | -4,6 |
| sniper | +105,5 | +73,1 | +0,4 | +178,4 | -0,0 | | -1,0 | -2,0 |
| marginal | +83,2 | +42,1 | +20,6 | +87,3 | +15,2 | +15,5 | | -0,5 |
| lecteur | +70,9 | +44,9 | +29,8 | +88,2 | +19,8 | +15,5 | +2,7 | |

### À 5 joueurs

| Candidat \ adversaires | aléatoire | heuristique | bayésien | agressif | passif | sniper | marginal | lecteur |
|---|---|---|---|---|---|---|---|---|
| aléatoire | | -35,0 | -29,2 | +81,0 | -24,1 | -54,2 | -80,2 | -49,7 |
| heuristique | +26,1 | | -24,0 | +59,7 | -29,8 | -37,0 | -27,1 | -20,0 |
| bayésien | +49,2 | +31,3 | | +100,7 | -0,1 | +6,1 | +0,2 | +2,9 |
| agressif | -105,6 | -58,4 | -96,8 | | -99,7 | -118,4 | -86,8 | -57,8 |
| passif | +42,3 | +29,0 | -6,5 | +81,0 | | +0,1 | -4,2 | +0,7 |
| sniper | +95,9 | +79,2 | +0,4 | +183,0 | -0,1 | | -1,0 | -1,1 |
| marginal | +82,0 | +43,0 | +21,7 | +81,7 | +13,7 | +17,3 | | +7,3 |
| lecteur | +66,5 | +47,3 | +34,6 | +82,0 | +18,7 | +15,0 | +0,7 | |

Les cases des anciens bots entre eux sont identiques à la phase 2. J'ai aussi vérifié, donne par donne, que le marginal joue exactement comme le code de l'étiquette `phase2-figgie`.

### La référence, phase 2 contre phase 3

| Contre | Marginal (4 j.) | Lecteur (4 j.) | Marginal (5 j.) | Lecteur (5 j.) |
|---|---|---|---|---|
| aléatoire | +83,2 | +70,9 | +82,0 | +66,5 |
| heuristique | +42,1 | +44,9 | +43,0 | +47,3 |
| bayésien | +20,6 | +29,8 | +21,7 | +34,6 |
| agressif | +87,3 | +88,2 | +81,7 | +82,0 |
| passif | +15,2 | +19,8 [+18,5 ; +21,2] | +13,7 | +18,7 [+17,6 ; +19,8] |
| sniper | +15,5 | +15,5 | +17,3 | +15,0 |
| marginal | | +2,7 [+1,8 ; +3,7] | | +0,7 [-0,3 ; +1,7] |

À 4 joueurs, le lecteur passe la règle d'entrée, qui demande maintenant de battre l'heuristique, le sniper, le bayésien et le marginal. Il gagne contre tout le zoo, et son pire cas est le marginal, à +2,7 $ par manche.

À 5 joueurs, il échoue. Contre le marginal, il ne gagne que +0,7 $, et l'intervalle contient zéro. Surtout, la table s'inverse quand les lecteurs sont nombreux : un marginal seul face à quatre lecteurs gagne +7,3 $ par manche ([+6,0 ; +8,7]), et un bayésien seul face à quatre lecteurs +2,9 $.

Le lecteur n'est donc pas promu. Le marginal reste le bot de référence. Le lecteur rejoint le zoo comme adversaire.

### D'où viennent les gains : le marginal corrigé

Pour séparer les deux améliorations du lecteur, j'ai mesuré un troisième bot : le marginal avec le seul comptage corrigé, sans lecture du marché. Contre le marginal d'origine, il fait +0,5 $ à 4 joueurs et -0,3 $ à 5, deux résultats dont l'intervalle contient zéro. Le comptage corrigé devine beaucoup mieux la couleur objectif, mais ne rapporte presque rien à lui seul. Le petit gain du lecteur à 4 joueurs vient donc surtout de la lecture des cotations.

### La mémoire

L'expérience la plus importante pour l'objectif du projet compare deux lecteurs sur des parties de 10 manches. La table est mixte : un aléatoire, un heuristique, un marginal. Le premier lecteur garde sa mémoire des adversaires d'une manche à l'autre, le second oublie tout à chaque manche. 200 parties, en donnes dupliquées.

| Manche | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 |
|---|---|---|---|---|---|---|---|---|---|---|
| Avec mémoire | +41,6 | +40,2 | +41,2 | +40,9 | +40,7 | +35,9 | +44,9 | +41,3 | +40,0 | +39,5 |
| Sans mémoire | +41,6 | +39,5 | +37,4 | +40,3 | +42,5 | +34,9 | +41,8 | +39,6 | +41,1 | +39,3 |
| Écart | 0,0 | +0,7 | +3,8 | +0,6 | -1,8 | +1,0 | +3,1 | +1,7 | -1,2 | +0,3 |

À la première manche, les deux versions font exactement le même résultat, puisque ni l'une ni l'autre n'a encore rien appris. Ensuite, l'écart moyen des manches 2 à 10 est de +0,92 $ par manche, avec un intervalle [-0,33 ; +2,18] qui contient zéro. Le lecteur apprend bien à juger ses adversaires : en fin de partie, il accorde 0,62 de confiance à l'aléatoire, contre 0,96 à l'heuristique et 0,91 au marginal. Mais ça ne se traduit pas en dollars de façon mesurable.

## Ce que j'en retiens

Mieux deviner ne suffit pas à mieux gagner. Le lecteur trouve la couleur objectif dans 52 % des cas à une minute, contre 42 % pour le marginal, et ça ne rapporte que 2,7 $ par manche à 4 joueurs. La raison est sans doute celle de la phase 2 : le marginal gagne surtout en prenant les erreurs des autres dans les premières secondes, et le marché meurt toujours vers 16 secondes. Une meilleure information arrive quand il n'y a presque plus rien à échanger.

Les lecteurs se gênent entre eux. Quand ils sont majoritaires à la table, ils lisent les signaux les uns des autres, et ces signaux viennent de bots qui eux-mêmes lisent le marché. Le modèle a appris sur des tables où personne ne lisait le marché. À une table de lecteurs, ce qu'il a appris ne correspond plus à ce qu'il voit. Un marginal qui ignore tout ça en profite. C'est exactement le problème qu'une ligue d'auto-jeu, en phase 4, doit traiter : réapprendre le modèle sur des parties où le lecteur joue contre lui-même.

Apprendre à qui se fier fonctionne, mais rapporte peu ici. Dans le zoo, les signaux de presque tous les adversaires sont utiles, et l'aléatoire lui-même n'est sans doute pas si trompeur : il ne peut proposer de vendre que des cartes qu'il possède, ce qui révèle un peu sa main. La mémoire servira davantage face à des adversaires trompeurs, et ceux-là arriveront en phase 4.

Mesurer la calibration a payé plus que tout le reste. Sans le tableau « quand le bot annonce 80 %, a-t-il raison 80 % du temps ? », je n'aurais jamais trouvé le défaut du comptage, présent depuis la phase 2.

## Limites

Tous les adversaires sont des bots que j'ai écrits, et le modèle de signaux a appris sur eux. Face à des humains, qui cotent autrement, les rapports appris seraient faux. Il faudra les réapprendre sur de vraies parties si la phase 5 le permet.

Le modèle traite les événements comme indépendants, alors qu'ils ne le sont pas : un joueur qui propose 10 $ puis 12 $ pour un cœur suit la même idée. Le dédoublonnage limite ce problème sans le supprimer.

Le lecteur utilise le spread de 8 $ réglé pour le marginal. Je ne l'ai pas réglé de nouveau pour lui, et un autre réglage pourrait changer le verdict à 5 joueurs.

Les parties de plusieurs manches repartent de 350 $ à chaque manche, alors que sur figgie.com l'argent se cumule.

Les limites des phases précédentes tiennent toujours : temps de réaction inventés, quatre règles du site supposées.

## Reproduire

```bash
cd projets/bot-figgie
python3 -m unittest                                         # les 74 tests, une seconde
python3 -m figgie.learn --train 4000 --valid 1000           # apprendre le modèle, environ 30 s sur 10 cœurs
python3 -m figgie.memoire --deals 200 --rounds 10           # l'expérience sur la mémoire, environ 5 minutes
python3 -m figgie.evaluate --candidate lecteur --deals 1000 --seed 1
```

Le modèle appris est enregistré dans `modeles/signaux.json`. Pour revenir exactement au code de cette phase : `git checkout phase3-figgie`.

## Et ensuite

La phase 4 doit traiter ce que la phase 3 a révélé : des bots qui se font exploiter quand ils sont nombreux à la table. Elle fera jouer le bot contre ses propres versions et contre des adversaires entraînés à le battre, et réapprendra le modèle de signaux sur ces parties-là.
