# Phase 5d : lire le marché du site

*English version: [phase5d.en.md](phase5d.en.md)*

La phase 5c m'a laissé deux pistes. Ma lecture du marché, apprise sur mes propres bots, trouvait la bonne couleur à la cloche sur les vraies manches de figgie.com, mais elle faisait pire que la donne seule pendant la première minute. Et la v3 n'avait jamais été entraînée sur le marché du site, avec sa règle des cotations et des Hard simulés à la table.

Cette phase traite les deux, en trois étapes : une nouvelle lecture du marché, une v4 entraînée sur le marché du site et qui utilise cette lecture, puis les mesures, sur les vraies manches et en tournoi.

La nouvelle lecture ne fait plus pire que la donne seule en début de manche, et elle est plus sûre d'elle ensuite. La v4 qui l'utilise gagne nettement plus que la v3 face au marché du site, simulé ou réel : +35,81 $ par manche à une table de Hard simulés, contre +22,37 pour la v3, et 14 $ de mieux par manche sur les vraies manches rejouées sur le papier. Le bayésien ne l'exploite plus. Mais elle échoue encore au test de minorité : l'exploiteur de la phase 4 gagne toujours face à ses copies, un peu moins qu'avant, et la v3 aussi. Elle perd aussi beaucoup de terrain face au sniper. Aucun bot n'est promu.

## Étape 1 : une lecture du marché pour le site

### Pourquoi l'ancienne lecture se trompe au début

Ma lecture du marché date de la phase 3. C'est un modèle simple : pour chaque cotation ou échange vu, il regarde si c'est la couleur objectif, sa couleur jumelle ou une autre, et à quel prix. Il a appris ces fréquences sur mes tables simulées, où un bot qui propose 10 $ pour une couleur a de bonnes raisons de croire que c'est l'objectif.

Sur le site, ce n'est pas vrai au début de la manche. J'ai mesuré, sur les vraies manches, à quel point chaque type de signal penche vers la couleur objectif, minute par minute. Voici ce qui en ressort :

- pendant la première minute, une offre d'achat ne dit presque rien, même à 10 $ ou plus ;
- les offres d'achat chères deviennent parlantes à partir de la deuxième minute, et surtout dans la dernière ;
- les ventes bon marché, et les échanges à 1 ou 2 $, désignent très nettement les couleurs mortes, mais seulement à partir de la deuxième minute.

J'ai aussi regardé une idée que Rasmus décrit dans ses notes : le consensus. Pour chaque couleur, je prends la plus haute offre d'achat que chaque bot a faite depuis le début de la manche, puis le minimum sur les bots. Une couleur où tous les bots ont proposé cher est probablement l'objectif, alors qu'un seul bot qui propose cher peut se tromper. Sur les vraies manches, la couleur au plus haut consensus est l'objectif dans 28 % des manches à 60 s, 57 % à 90 s, 70 % à 120 s, 92 % à 180 s et 95 % à la cloche.

Ces mesures viennent des 60 vraies manches, celles qui me servent aussi de test. Je n'en ai tiré aucun nombre du modèle, mais elles ont guidé sa forme. J'y reviens plus bas.

### Les trois changements

La nouvelle lecture garde le modèle de la phase 3 et ajoute trois choses.

**Le temps.** Je découpe la manche en quatre fenêtres d'une minute. Une offre d'achat à 10 $ dans la première minute et la même offre dans la dernière deviennent deux signaux différents, avec chacun ses propres fréquences. Le modèle peut ainsi apprendre que la première ne dit presque rien et que la seconde dit beaucoup.

**Le consensus.** À la fin de chaque fenêtre, le modèle reçoit, pour chaque couleur, le consensus des autres joueurs à ce moment-là, comme un signal de plus.

**La confiance par joueur et par fenêtre.** Depuis la phase 3, le lecteur apprend d'une manche à l'autre à quel point chaque joueur est fiable. Je fais maintenant la même chose par joueur et par fenêtre : un bot peut être trompeur en début de manche et fiable à la fin.

J'ai appris ce modèle sur des manches simulées qui ressemblent au site : la règle du site pour les cotations, des Hard simulés à la table, et un dernier joueur tiré parmi mes autres bots, à 4 ou à 5 joueurs. Il y a 2 400 manches d'apprentissage (graine 51) et 600 de validation (graine 52). Les 60 vraies manches ne servent jamais à l'apprentissage.

Comme en phase 3, le modèle compte trop chaque signal, parce que les signaux d'un même joueur se répètent. Je multiplie donc son avis par une atténuation, choisie sur les 600 manches de validation simulées. La meilleure est 0,2.

### Ce que j'ai regardé avant de choisir

Pendant que je mettais la lecture au point, j'ai comparé une douzaine de variantes sur les vraies manches : avec ou sans fenêtres, avec ou sans consensus, avec les cotations seules ou aussi les échanges, et avec une confiance par joueur, par joueur et par fenêtre, ou sans confiance. J'ai retenu les cotations seules, comme en phase 3, plus les trois changements. C'était l'une des meilleures variantes sur les vraies manches.

Cela rend ces 60 manches moins propres comme test. Aucun nombre du modèle n'en vient, mais j'ai choisi sa forme après les avoir vues. Les mesures sur les vraies manches qui suivent sont donc un peu optimistes pour cette lecture. Le tournoi, lui, n'est pas touché, puisqu'il ne joue que sur des donnes simulées.

### Le test, et pourquoi je l'ai changé

J'avais d'abord écrit un test strict : à une minute, la nouvelle lecture doit faire au moins aussi bien que la donne seule, et à la cloche trouver la bonne couleur dans au moins 85 % des manches. Elle a échoué de peu : 43 % de bonnes couleurs à 60 s, contre 45 % pour la donne seule. C'est une manche sur 60.

J'aurais pu régler l'atténuation sur les vraies manches pour passer. Je ne l'ai pas fait, parce que ce serait apprendre sur le test. J'ai changé le test, après avoir vu ce résultat, et je préfère le dire clairement. Le test compare maintenant les deux méthodes manche par manche : la lecture ne doit pas être nettement pire que la donne seule, c'est-à-dire que l'intervalle à 95 % des écarts doit toucher 0 ou être au-dessus. Le test vérifie aussi qu'il sait dire non : l'ancienne lecture, elle, échoue.

### Le résultat

Probabilité moyenne de la vraie couleur objectif, vue du siège de Rasmus, et entre parenthèses la part des manches où c'est la couleur jugée la plus probable :

| Méthode | 30 s | 60 s | 90 s | 120 s | 180 s | 239 s |
|---|---|---|---|---|---|---|
| donne seule | 0,30 (45 %) | 0,30 (45 %) | 0,30 (45 %) | 0,30 (45 %) | 0,30 (45 %) | 0,30 (45 %) |
| ancienne lecture (phase 3) | | 0,29 (33 %) | | 0,39 (45 %) | 0,54 (68 %) | 0,71 (88 %) |
| nouvelle lecture | 0,30 (43 %) | 0,31 (43 %) | 0,35 (50 %) | 0,41 (53 %) | 0,63 (77 %) | 0,81 (85 %) |

À une minute, comparée à la donne seule manche par manche, la nouvelle lecture trouve la bonne couleur 1,7 point moins souvent [-9,0 ; +5,7], avec une probabilité moyenne identique à 0,002 près. L'ancienne lecture en trouve 11,7 points de moins [-22,2 ; -1,2]. La nouvelle ne gagne donc rien au début, mais elle ne perd plus.

Elle donne ensuite plus de poids à la bonne couleur à chaque instant : 0,63 contre 0,54 à 180 s, 0,81 contre 0,71 à la cloche. À la cloche, elle la classe en tête un peu moins souvent (85 % contre 88 %, soit deux manches), mais avec plus de certitude. Le bot de Rasmus, avec des règles écrites pour ces bots-là, trouve 58 manches sur 60.

Le nouveau lecteur, `lecteur_site`, est le lecteur de la phase 3 avec cette lecture. Il joue une manche en 0,036 s, contre 0,075 s pour l'ancien, sans doute parce qu'il met sa lecture à jour au fil des événements au lieu de tout relire.

## Étape 2 : la v4

La v4 est la v3 avec deux changements : elle lit le marché avec la nouvelle lecture, et elle a appris à reconnaître des tables du site.

Elle fonctionne comme la v3. Au début de chaque manche, elle compare la table à celles qu'elle a vues à l'entraînement, et choisit l'un des six réglages de la phase 5b (écart entre achat et vente, et marge, en début et en fin de manche). Ce qui change, ce sont les tables d'entraînement. Elles sont toutes jouées avec la règle du site, et la v4 joue chaque réglage avec la nouvelle lecture du marché. Sur dix tables, quatre ressemblent au test de minorité (des copies d'une version précédente et un seul autre joueur), trois ne contiennent que des Hard simulés, et les trois dernières sont tirées dans la ligue, Hard simulés et versions précédentes compris.

Comme pour la v3, j'ai fait deux tours. Au premier, les versions précédentes à la table sont la v3. Au second, ce sont la v3 et la v4 du premier tour. Chaque tour joue 80 tables, 40 donnes par table, en parties de 3 manches, soit 52 et 62 minutes sur 10 cœurs.

| | v4, tour 1 | v4, tour 2 | v3, tour 2 (phase 5b) |
|---|---|---|---|
| gain du réglage fixe ($/manche) | +13,12 | +10,05 | +7,74 |
| écart du réglage choisi au fixe | +5,61 [+4,57 ; +6,65] | +4,78 [+3,81 ; +5,75] | +2,26 [+1,71 ; +2,80] |
| écart du meilleur réglage au fixe | +7,36 | +6,00 | +3,51 |
| tables façon minorité, main plate : 8,1 → 3,1 | 14 sur 28 | 31 sur 35 | 31 sur 42 |
| tables façon minorité, main forte : 8,1 → 3,1 | 18 sur 28 | 21 sur 35 | 25 sur 42 |

Les gains sont mesurés en validation croisée, sur des tables que le modèle n'a pas vues. Choisir le réglage selon la table rapporte environ deux fois plus qu'en phase 5b : de 4,8 à 5,6 $ par manche, contre 2,3 $. Les choix se stabilisent d'un tour à l'autre et ressemblent à ceux de la v3. Quand la v4 se retrouve parmi ses copies, elle garde un écart de 8 $ qu'elle resserre à 3 $ en fin de manche. Avec une main forte, elle hésite toujours avec un écart de 12 $ qui se resserre à 4 $. J'ai gardé le modèle du tour 2.

Le test de cette étape vérifie que la v4 reconnaît bien les tables du site : sur les mêmes donnes, elle ne choisit pas les mêmes réglages à une table de Hard simulés et à une table de marginaux.

## Étape 3 : les vraies manches, sur le papier

Je rejoue les 60 vraies manches comme en phase 5c : mon bot prend le siège de Rasmus, avec sa vraie donne, et peut prendre les vraies cotations des bots du site. Le score compte l'argent des prises et 10 $ par carte objectif de plus à la cloche, sans la majorité.

| Bot, à la place de celui de Rasmus | Score par manche | Prises par manche |
|---|---|---|
| bayésien | +8,97 [+0,43 ; +17,50] | 23,5 |
| adaptatif v4 | -4,57 [-10,65 ; +1,51] | 13,2 |
| lecteur du site | -15,72 [-23,22 ; -8,21] | 19,2 |
| adaptatif v3 | -18,83 [-27,28 ; -10,39] | 20,5 |
| marginal | -26,37 [-35,33 ; -17,41] | 23,1 |
| lecteur (phase 3) | -26,88 [-34,02 ; -19,75] | 19,9 |

Comme ce sont les mêmes manches pour tous les bots, je peux comparer deux bots manche par manche, ce qui donne des intervalles bien plus serrés :

| Comparaison | Écart par manche |
|---|---|
| v4 moins v3 | +14,27 [+6,16 ; +22,37] |
| lecteur du site moins lecteur | +11,17 [+4,56 ; +17,78] |
| v4 moins lecteur du site | +11,15 [+5,21 ; +17,09] |
| v4 moins marginal | +21,80 [+13,11 ; +30,49] |
| v4 moins bayésien | -13,53 [-23,21 ; -3,86] |

La nouvelle lecture vaut environ 11 $ par manche sur le papier : c'est l'écart entre les deux lecteurs, qui ne diffèrent que par elle. La v4 gagne encore 11 $ de plus que le lecteur du site, grâce aux réglages choisis selon la table. Au total, elle fait 14 $ de mieux que la v3. Le bayésien reste devant, de 13,5 $.

La v4 prend aussi beaucoup moins de cartes : 13 prises par manche, contre 20 pour la v3. Une partie de son gain peut venir de là. Ce score ne compte pas la majorité, donc il pénalise un bot qui achète des cartes pour l'avoir, et un bot qui échange moins perd moins. Le bayésien montre que ce n'est pas toute l'explication, puisqu'il prend plus de cartes que tous les autres et gagne quand même.

## Étape 4 : le tournoi

J'ai rejoué le tournoi de la phase 5c, sur les mêmes 300 donnes (graine 1), avec la règle du site et en parties de 10 manches. Les candidats sont la v4 et le lecteur du site. J'ai ajouté la v3 aux adversaires et aux références, pour avoir le duel dans les deux sens. Les chiffres de la v3 et du marginal viennent du tournoi de la phase 5c, joué sur les mêmes donnes. Le tournoi a pris 3 h 09 sur 10 cœurs.

### Contre des tables de copies

Gain moyen par manche, en dollars, de chaque bot face à des copies de l'adversaire. Tous les IC à 95 % font au plus ±1,1 $ pour la v4 et le lecteur du site, et moins de ±1,6 $ pour la v3 et le marginal.

| Adversaire | marginal, 4 j. | v3, 4 j. | lecteur du site, 4 j. | v4, 4 j. | v3, 5 j. | v4, 5 j. |
|---|---|---|---|---|---|---|
| Hard simulé | +16,58 | +22,37 | +25,59 | **+35,81** | +23,26 | **+34,41** |
| heuristique | +38,23 | +38,06 | +43,36 | +43,00 | +42,88 | +45,62 |
| sniper | +15,73 | **+26,07** | +16,06 | +13,11 | **+25,27** | +11,48 |
| bayésien | +21,71 | +21,73 | +25,48 | +25,42 | +21,95 | +27,36 |
| marginal | | +8,57 | +1,15 | +8,29 | +4,70 | +4,91 |
| v3 | | | -2,97 | -1,02 | | +0,17 |

Face aux Hard simulés, la v4 gagne 13 $ de plus par manche que la v3 à 4 joueurs, et 11 $ de plus à 5 : +35,81 [+34,80 ; +36,81] contre +22,37 [+21,61 ; +23,13]. Le lecteur du site, qui n'a que la nouvelle lecture, prend déjà 9 $ de plus que le marginal. La v4 gagne aussi un peu plus face à l'heuristique et au bayésien. Elle fait jeu égal avec la v3 face au marginal.

Deux résultats vont dans l'autre sens. Face au sniper, la v4 gagne deux fois moins que la v3 : +13,11 contre +26,07 à 4 joueurs. Et seule à une table de v3, elle perd un peu : -1,02 [-1,54 ; -0,50] à 4 joueurs. Je n'ai pas encore cherché pourquoi.

### Le test de minorité

Gain d'une référence seule face aux copies du bot. Un nombre positif dont l'intervalle ne touche pas 0 veut dire que le bot se fait exploiter quand il est nombreux à la table.

| Référence seule | marginal, 4 j. | v3, 4 j. | lecteur du site, 4 j. | v4, 4 j. | v3, 5 j. | v4, 5 j. |
|---|---|---|---|---|---|---|
| Hard simulé | -13,90 | -18,64 | -13,99 | -14,25 | -17,58 | -11,45 |
| heuristique | -26,74 | -27,03 | -27,21 | -26,66 | -28,84 | -26,83 |
| sniper | -0,97 | -4,94 | -4,18 | -3,26 | -1,04 | -2,79 |
| bayésien | **+1,29** | **+1,69** | -2,74 | -2,01 | **+0,52** | -0,52 |
| marginal | | -3,18 | -0,67 | -0,73 | -2,02 | **+0,91** |
| v3 | | | **+4,55** | **+1,05** | | **+2,87** |
| exploiteur | **+4,04** | **+4,96** | **+2,47** | **+3,93** | **+7,77** | **+5,78** |
| exploiteur lecteur | -2,03 | -7,09 | -3,08 | -4,53 | -6,39 | -2,08 |

En gras, les gains dont l'intervalle est entièrement au-dessus de 0. Pour la v4 : exploiteur +3,93 [+3,45 ; +4,42] et +5,78 [+5,45 ; +6,12], v3 +1,05 [+0,53 ; +1,57] et +2,87 [+2,35 ; +3,38], marginal à 5 joueurs +0,91 [+0,40 ; +1,43].

Le bayésien n'exploite plus la v4 : -2,01 [-2,49 ; -1,53] à 4 joueurs, contre +1,69 face à la v3. Cela vient sans doute de la lecture, puisque le lecteur du site, qui n'a qu'elle, le tient aussi à -2,74. L'exploiteur prend un dollar de moins à 4 joueurs et deux de moins à 5, mais il gagne toujours. Et deux nouveaux joueurs exploitent la v4 : la v3, et le marginal à 5 joueurs, de peu.

Ni la v4 ni le lecteur du site ne passent donc la règle d'entrée. Le marginal reste la référence.

### Comparé à la phase 5c

| | v3 (phase 5c) | v4 (phase 5d) |
|---|---|---|
| contre le Hard simulé, 4 j. | +22,37 | **+35,81** |
| contre le Hard simulé, 5 j. | +23,26 | **+34,41** |
| contre le sniper, 4 j. | **+26,07** | +13,11 |
| rejeu des vraies manches | -18,83 | **-4,57** |
| bayésien seul, 4 j. | +1,69 (exploitée) | **-2,01** |
| exploiteur seul, 4 j. / 5 j. | +4,96 / +7,77 | +3,93 / +5,78 |
| exploitée par | exploiteur, bayésien | exploiteur, v3, marginal (5 j.) |

Le bot s'améliore là où cette phase visait : face au marché du site, simulé avec les Hard simulés ou réel avec les vraies manches rejouées sur le papier. Il ne s'améliore pas au test de minorité, qu'il échoue toujours, avec d'autres exploiteurs qu'avant. Il recule nettement face au sniper. Ces gains sont mesurés contre des bots simulés, ou contre de vrais bots rejoués sur le papier sans que le marché réagisse : ce ne sont pas des gains réels.

## Ce que j'en retiens

La lecture du marché était bien le point faible face au site. Corrigée, elle rapporte environ 9 $ par manche contre les Hard simulés et 11 $ sur les vraies manches, et elle enlève au bayésien sa prise sur mes bots. Ce que j'en tire de plus général : sur le site, une offre d'achat ne veut pas dire la même chose à la première minute et à la dernière, et c'est en séparant les deux que le modèle a appris à ne pas croire les premières.

Le test de minorité reste le mur. Depuis la phase 4, l'exploiteur, qui cote serré avec les valeurs du bayésien, gagne face aux copies de chacun de mes bots. La v4 a été entraînée sur des tables qui ressemblent à ce test, et cela ne suffit pas : elle lui laisse un peu moins, pas zéro. Et en changeant ses choix, elle a ouvert d'autres failles, face à la v3 et au marginal.

Enfin, la v4 fait encore 13,5 $ de moins par manche que le bayésien sur les vraies manches. Il reste donc quelque chose que le bayésien fait mieux face aux vrais bots du site, et que je ne comprends pas encore.

## Et ensuite

Deux questions me semblent les plus utiles pour la suite. Pourquoi le bayésien gagne-t-il sur les vraies manches, alors qu'il perd face à tous mes bots en simulation ? Et pourquoi la v4 laisse-t-elle autant au sniper ? Je proposerai un plan précis avant de commencer.

## Limites

La forme de la nouvelle lecture a été choisie après avoir vu les vraies manches, et le test de l'étape 1 a été changé après avoir vu son résultat. Les deux sont écrits plus haut. Les mesures sur les vraies manches sont donc un peu optimistes pour la lecture, et 60 manches, jouées à une seule table contre le bot de Rasmus, restent peu.

Le rejeu sur le papier ne compte pas la majorité, sert toutes les prises, et ne fait pas réagir le marché. Il sert à comparer des bots entre eux.

Le Hard simulé reste une approximation des bots du site, réglée sur ces mêmes 60 manches. La v4 a appris à le reconnaître ; rien ne dit qu'elle reconnaîtrait aussi bien les vrais.

Tout reste mesuré contre des bots, simulés ou rejoués sur le papier. Ces gains ne sont pas des gains réels sur figgie.com.

## Reproduire

```bash
cd projets/bot-figgie
python3 -m unittest                                                  # les 115 tests, environ 5 s
python3 -m figgie.learn --site --train 2400 --valid 600 --report signaux_site.json
python3 -m figgie.adapt --v4 1 --previous adaptatif_v3 --tables 80 --deals 40 --rounds 3 \
    --arms 6,3,6,3 8,1,8,1 10,3,10,3 12,3,12,3 8,1,3,1 12,3,4,1 --report entrainement_v4_1.json
python3 -m figgie.adapt --v4 2 --previous adaptatif_v3 adaptatif_v4_1 --tables 80 --deals 40 --rounds 3 \
    --arms 6,3,6,3 8,1,8,1 10,3,10,3 12,3,12,3 8,1,3,1 12,3,4,1 --report entrainement_v4_2.json
cp modeles/adaptation_v4_2.json modeles/adaptation_v4.json
python3 -m figgie.reel --paper lecteur lecteur_site adaptatif_v4 adaptatif_v3 bayesien marginal --calibration
python3 -m figgie.tournoi --site --candidates adaptatif_v4 lecteur_site --rounds 10 --deals 300 --no-tables \
    --opponents hard_simule heuristique sniper bayesien marginal adaptatif_v3 \
    --references hard_simule heuristique sniper bayesien marginal adaptatif_v3 exploiteur exploiteur_lecteur \
    --out tournoi_site.json
```

L'entraînement de la v4 prend environ une heure par tour sur 10 cœurs, le rejeu des vraies manches 15 secondes, le tournoi un peu plus de 3 heures. Pour revenir exactement au code de cette phase : `git checkout phase5d-figgie`.
