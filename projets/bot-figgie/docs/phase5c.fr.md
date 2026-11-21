# Phase 5c : un marché plus proche du site

*English version: [phase5c.en.md](phase5c.en.md)*

Jusqu'ici, tous mes bots ont appris et été mesurés sur un marché que j'ai inventé. Les journaux de vraies parties publiés par Rasmus Suonio ont montré en phase 5b à quel point ce marché est loin de figgie.com : 53 échanges par manche sur le site, presque la moitié dans la dernière minute, contre 6 à 22 sur mes tables, tous dans la première minute. Un bot réglé sur mes tables est réglé pour un jeu qui n'existe pas.

Cette phase rapproche le simulateur du site en quatre étapes : la règle du site pour les cotations, un adversaire simulé réglé sur les vrais bots du site, le rejeu des vraies manches avec nos bots, et un tournoi sur ce nouveau marché.

Le Hard simulé ressemble au site bien plus que mes tables d'avant, sans en être une copie. Sur ce nouveau marché, la v3 reste le meilleur de mes bots adaptatifs : elle prend 22 à 23 $ par manche à une table de Hard simulés, contre 20 $ pour la v2 et 17 à 19 $ pour le marginal. Mais elle échoue toujours au test de minorité, face aux mêmes adversaires qu'en phase 5b, et aucun bot n'est promu. Le rejeu des vraies manches donne un autre classement : face aux vrais bots du site, rejoués sur le papier, seul le bayésien gagne, et la v3 et le marginal perdent.

## D'où viennent les données

Rasmus Suonio a écrit un bot qui joue sur figgie.com contre les bots « Hard » du site, et il a publié ses journaux sous licence MIT. Il y a 60 manches, jouées à 4 joueurs : son bot et trois bots Hard. Chaque cotation, chaque retrait et chaque échange vu par son bot y est noté, à la seconde près. J'ai copié ces fichiers dans `donnees/rasmus/`, avec sa licence.

Je n'ai rien lancé moi-même sur figgie.com. Toutes les mesures de cette phase sont faites sur ces journaux ou dans mon simulateur.

## Étape 1 : la règle du site pour les cotations

Sur le site, il n'y a qu'une offre d'achat et une offre de vente affichées par couleur. Une nouvelle offre doit battre celle qui est affichée, et elle la remplace. Mon simulateur, lui, gardait une cotation par joueur. J'ai lu la règle dans le code de Rasmus, qui l'applique comme l'interface du site, et je l'ai ajoutée au moteur en option (`single_quote`). Elle est désactivée par défaut, pour que les résultats des phases précédentes ne bougent pas, et le test de référence le vérifie.

Le premier essai a montré que mes bots ne connaissaient pas cette règle. Quand leur offre était battue, ils la renvoyaient sans fin, et le moteur la refusait à chaque fois : une table de marginaux faisait environ 2 300 actions refusées par manche, contre 4 sans la règle. Mes bots savent maintenant qu'une offre doit battre celle qui est affichée. Ils n'envoient plus une offre qui serait refusée, et ils retirent leur cotation quand ils voudraient reculer leur prix. Il ne reste qu'une quinzaine de refus par manche, dus au marché qui bouge pendant qu'une action est en route.

Avec cette règle, une cotation acceptée par mon moteur est une nouvelle meilleure offre, exactement comme une cotation des journaux. Les deux se comparent directement.

## Étape 2 : un bot Hard simulé

### Ce que font les vrais bots

J'ai mesuré les trois bots Hard des journaux, en laissant de côté le bot de Rasmus :

| Mesure | figgie.com | table de 4 marginaux, règle du site |
|---|---|---|
| échanges par manche et par paire de bots Hard | 9,4 | 1,0 |
| part des échanges dans chaque minute | 12 / 19 / 25 / 44 % | 100 / 0 / 0 / 0 % |
| cotations par minute et par bot | 37,8 | 2,8 |
| première cotation | 5 s | 0,6 s |
| prix médian d'un échange, couleur objectif | 7 $ | |
| prix médian d'un échange, autres couleurs | 3 $ | |
| plus haut prix d'achat d'un bot, couleur objectif | 10 $ | |
| plus haut prix d'achat d'un bot, autres couleurs | 5 $ | |

Médianes par bot, sauf les deux premières lignes. Je compte les échanges par paire de bots Hard, parce que les journaux ont 3 bots Hard et que mes tables simulées en ont 4.

Les journaux montrent aussi comment les bots du site cotent. Ils montent leur offre d'achat d'un dollar à la fois au-dessus de la meilleure (1 $, puis 2 $, puis 3 $), et descendent leur offre de vente de la même façon. Ils cotent sans arrêt. Ils ne sont pas d'accord entre eux : 88 % des cartes bradées à 1 ou 2 $ par un bot Hard sont suivies, dans les 45 secondes, d'une offre de rachat 2 $ plus chère par un autre bot Hard.

### Le bot que j'ai écrit

Mon Hard simulé fait la même chose. Il estime ce que vaut une carte de chaque couleur : une base, plus un montant fois la probabilité que ce soit la couleur objectif, d'après sa donne et les cartes échangées. Il monte son offre d'achat d'un dollar au-dessus de la meilleure, jusqu'à sa valeur moins une marge, et descend sa vente jusqu'à sa valeur plus la marge. Cette marge fond au fil de la manche. Chaque valeur reçoit un écart tiré au hasard, retiré après chaque échange. Enfin, il lit le marché : une couleur où les autres ont proposé plus cher devient plus probablement l'objectif, parce que, d'après Rasmus, ce sont les plus hautes offres d'achat qui désignent l'objectif sur le site.

J'ai réglé ses huit paramètres par une recherche au hasard. J'ai tiré 3 000 réglages et joué chacun sur 30 manches à 4 Hard simulés (graine 31). J'ai gardé les 10 plus proches du site, et je les ai revérifiés sur 90 autres manches (graine 32). L'écart au site est une somme de carrés, où chaque mesure est ramenée à une échelle fixée à la main (par exemple 2 échanges par paire, 8 cotations par minute, 1 $ pour un prix).

Il a fallu trois versions du bot. Sans écart au hasard, mes Hard simulés étaient presque toujours d'accord et n'échangeaient presque pas : 0,7 échange par paire, contre 9,4 sur le site. Avec l'écart, le nombre d'échanges montait, mais les prix tombaient à 1 ou 2 $ et la couleur objectif ne se distinguait plus. Lire le marché par le prix des échanges aidait un peu. Lire les plus hautes offres d'achat, comme le décrit Rasmus, ne fait guère mieux : le meilleur réglage ne lit le marché que très peu (read = 0,05), et le deuxième, presque aussi proche du site, ne le lit pas du tout. Voici le réglage retenu :

| Mesure | figgie.com | Hard simulé |
|---|---|---|
| échanges par manche et par paire de bots | 9,4 | 6,5 |
| part des échanges dans chaque minute | 12 / 19 / 25 / 44 % | 16 / 19 / 25 / 40 % |
| cotations par minute et par bot | 37,8 | 53,3 |
| première cotation | 5,0 s | 5,6 s |
| prix médian, couleur objectif | 7 $ | 9 $ |
| prix médian, autres couleurs | 3 $ | 3 $ |
| plus haut prix d'achat, couleur objectif | 10 $ | 8 $ |
| plus haut prix d'achat, autres couleurs | 5 $ | 6 $ |

Mesuré sur les 90 manches de vérification.

Le Hard simulé n'est pas une copie des bots du site. Il échange un tiers de moins, cote plus souvent, et un compromis reste : plus il échange, moins bien il distingue la couleur objectif. Mais il ressemble beaucoup plus au site que mes tables d'avant. Les échanges s'étalent sur toute la manche et s'accélèrent vers la fin, la couleur objectif se vend plus cher que les autres, et chaque mesure est entre 0,6 et 1,5 fois celle du site. Un test vérifie ces deux conditions sur d'autres donnes, et vérifie aussi qu'une table de marginaux ne les remplit pas.

## Étape 3 : rejouer les vraies manches

### Sur le papier

Le paper_bot de Rasmus rejoue une vraie manche avec un autre bot à la place du sien. J'ai écrit la même chose pour mes bots. Mon bot prend le siège de Rasmus, avec sa vraie donne. Le carnet est celui du journal, et mon bot peut prendre les vraies cotations des bots du site. Ses propres cotations ne sont jamais servies, et le marché ne réagit pas à ce qu'il fait.

Le score d'une manche est l'argent gagné ou perdu sur ces prises, plus 10 $ par carte objectif de plus à la cloche. Il a deux défauts, que Rasmus signale aussi. La majorité, qui vaut 100 ou 120 $, n'est pas comptée, faute de connaître les mains des autres joueurs. Et chaque prise est servie, alors qu'en vrai un bot du site serait parfois plus rapide. Ce score sert donc à comparer des bots entre eux, pas à dire combien ils gagneraient.

Rejouer un marché qui ne réagit pas crée aussi des situations impossibles. Mon bot peut acheter une carte qu'un bot du site revendra ensuite pour de vrai à un autre joueur. J'ai dû refuser les achats qui donneraient à mon bot plus de cartes que le paquet n'en contient, et rayer les vrais échanges de Rasmus qui ne peuvent plus avoir lieu (vendre une carte déjà vendue sur le papier, par exemple).

| Bot, à la place de celui de Rasmus | Score par manche | Prises par manche |
|---|---|---|
| bayésien | +8,97 [+0,43 ; +17,50] | 23,5 |
| adaptatif v3 | -18,83 [-27,28 ; -10,39] | 20,5 |
| marginal | -26,37 [-35,33 ; -17,41] | 23,1 |
| lecteur | -26,88 [-34,02 ; -19,75] | 19,9 |
| Hard simulé | -37,15 [-45,51 ; -28,79] | 17,4 |
| heuristique | -41,83 [-56,72 ; -26,95] | 23,4 |

Sur les 60 vraies manches. La v3 garde sa mémoire d'une manche à l'autre, dans chacune des 6 séries de manches jouées à la même table.

Le bayésien est le seul à gagner nettement sur le papier. Le marginal et le lecteur perdent, mais ce score les désavantage : ils paient plus cher les cartes qui peuvent leur donner la majorité, et la majorité n'est pas comptée. La v3 perd moins que le marginal, alors que les deux ont le même calcul de valeur. Elle a donc choisi, au fil des manches, des réglages qui conviennent mieux à ces vrais bots. Mon Hard simulé perd beaucoup : l'écart tiré au hasard qui le fait ressembler aux bots du site lui fait aussi prendre de mauvais prix.

### Les probabilités sont-elles justes ?

J'ai aussi regardé, du siège de Rasmus, la probabilité que chaque méthode donne à la vraie couleur objectif, au fil de la manche :

| Méthode | 0 s | 60 s | 120 s | 180 s | 239 s |
|---|---|---|---|---|---|
| donne seule | 0,30 (45 %) | 0,30 (45 %) | 0,30 (45 %) | 0,30 (45 %) | 0,30 (45 %) |
| comptage des cartes (marginal) | 0,30 (45 %) | 0,30 (45 %) | 0,31 (47 %) | 0,31 (47 %) | 0,31 (45 %) |
| comptage et lecture du marché (lecteur) | 0,30 (45 %) | 0,29 (33 %) | 0,39 (45 %) | 0,54 (68 %) | 0,71 (88 %) |

Probabilité moyenne de la vraie couleur, et entre parenthèses la part des manches où c'est la couleur jugée la plus probable.

Trois choses en ressortent. Le comptage des cartes n'apprend presque rien sur le vrai marché, comme sur le mien en phase 5b. La lecture du marché, elle, marche sur le site alors qu'elle n'a appris que sur mes bots : à la cloche, elle trouve la bonne couleur dans 88 % des manches. Le bot de Rasmus, qui lit le marché avec des règles faites pour ces bots-là, en trouve 58 sur 60. Enfin, la lecture se trompe en début de manche : à une minute, elle fait moins bien que la donne seule, parce que les bots du site proposent souvent 10 à 15 $ pour des couleurs mortes.

## Étape 4 : le tournoi sur le nouveau marché

J'ai rejoué le tournoi de la phase 5b avec la règle du site, sur les mêmes 300 donnes dupliquées (graine 1), en parties de 10 manches. Pour qu'il tienne en un après-midi (3 h 25 sur 10 cœurs), je n'ai gardé comme adversaires que le Hard simulé, l'heuristique, le sniper, le bayésien et le marginal, et j'ai sauté les tables de comportements anormaux. Le test de minorité garde toutes ses références, plus le Hard simulé.

### Contre des tables de copies

Gain moyen par manche, en dollars, de chaque bot face à des copies de l'adversaire. Tous les IC à 95 % font moins de ±1,6 $.

| Adversaire | marginal, 4 j. | v2, 4 j. | v3, 4 j. | marginal, 5 j. | v2, 5 j. | v3, 5 j. |
|---|---|---|---|---|---|---|
| Hard simulé | +16,58 | +20,03 | +22,37 | +19,11 | +19,79 | +23,26 |
| heuristique | +38,23 | +38,16 | +38,06 | +42,11 | +42,11 | +42,88 |
| sniper | +15,73 | +16,80 | +26,07 | +17,06 | +17,70 | +25,27 |
| bayésien | +21,71 | +21,71 | +21,73 | +22,31 | +22,19 | +21,95 |
| marginal | | +1,95 | +8,57 | | +3,09 | +4,70 |

À une table de Hard simulés, la v3 gagne plus que la v2, qui gagne plus que le marginal. À 4 joueurs, les intervalles ne se touchent pas : +22,37 [+21,61 ; +23,13] pour la v3, +20,03 [+19,17 ; +20,89] pour la v2, +16,58 [+15,75 ; +17,40] pour le marginal.

### Le test de minorité

Gain d'une référence seule face aux copies du bot. Un nombre positif dont l'intervalle ne touche pas 0 veut dire que le bot se fait exploiter quand il est nombreux à la table.

| Référence seule | marginal, 4 j. | v2, 4 j. | v3, 4 j. | marginal, 5 j. | v2, 5 j. | v3, 5 j. |
|---|---|---|---|---|---|---|
| Hard simulé | -13,90 | -13,79 | -18,64 | -15,97 | -16,27 | -17,58 |
| heuristique | -26,74 | -26,66 | -27,03 | -28,75 | -28,60 | -28,84 |
| sniper | -0,97 | **+3,71** | -4,94 | -1,15 | **+2,93** | -1,04 |
| bayésien | **+1,29** | **+0,90** | **+1,69** | -0,26 | -0,60 | **+0,52** |
| marginal | | **+1,36** | -3,18 | | -0,00 | -2,02 |
| exploiteur | **+4,04** | **+1,46** | **+4,96** | **+6,99** | **+3,12** | **+7,77** |
| exploiteur lecteur | -2,03 | -4,65 | -7,09 | -3,75 | -5,62 | -6,39 |

En gras, les gains dont l'intervalle est entièrement au-dessus de 0. Pour la v3 : bayésien +1,69 [+1,06 ; +2,32] et +0,52 [+0,10 ; +0,93], exploiteur +4,96 [+4,51 ; +5,41] et +7,77 [+7,45 ; +8,09].

Aucun des trois bots ne passe la règle d'entrée. Tous battent nettement chaque référence, mais tous se font exploiter. Le Hard simulé, lui, perd beaucoup quand il est seul : 14 à 19 $ par manche.

### Comparé à la phase 5b

La v3 est le même bot qu'en phase 5b, avec le même modèle. Ce qui change, c'est le marché. Contre le zoo, la règle du site ne change presque rien, sur les mêmes donnes :

| v3, 4 joueurs | phase 5b, sans la règle | phase 5c, règle du site |
|---|---|---|
| contre le marginal | +8,48 | +8,57 |
| contre le sniper | +26,23 | +26,07 |
| exploiteur seul | +5,27 | +4,96 |
| bayésien seul | +1,43 | +1,69 |
| sniper seul | -4,86 | -4,94 |

C'est pareil pour le marginal (exploiteur seul : +4,32 en phase 5, +4,04 ici) et pour la v2 (sniper seul : +3,72 et +3,71). Un seul résultat change de côté : à 5 joueurs, le bayésien seul contre les copies de la v3 passe de +0,27 [-0,12 ; +0,67] à +0,52 [+0,10 ; +0,93]. C'est un petit écart, mais il fait passer le bayésien du côté des exploiteurs à 5 joueurs aussi.

Le bot ne s'améliore donc pas dans cette phase : je n'ai rien changé à la v3, et elle reste refusée pour les mêmes raisons. Ce que la phase apporte, c'est un marché de test plus proche du site, sur lequel la v3 reste devant la v2 et le marginal. Ces gains restent mesurés contre des bots simulés : ce ne sont pas des gains réels.

## Ce que j'en retiens

Le simulateur ressemble davantage au site, mais le classement de mes bots sur les tables simulées ne bouge pas. Le rejeu des vraies manches en donne un autre : le bayésien devant, puis la v3, puis le marginal. Le bayésien, que tous mes bots battent d'environ 22 $ par manche en simulation, est le seul à gagner sur le papier contre les vrais bots du site. Je vois deux explications et je ne peux pas encore trancher : soit mon simulateur récompense des choses que le site ne récompense pas, soit le score sur le papier avantage le bayésien parce qu'il ne compte pas la majorité.

La lecture du marché, apprise sur mes bots, marche sur les vrais bots en fin de manche : 88 % de bonnes couleurs à la cloche. En début de manche, elle se trompe, parce que les bots du site proposent cher pour des couleurs mortes. C'est la piste la plus concrète que cette phase m'a donnée.

Enfin, la v3 reste exploitée par l'exploiteur de la phase 4 et par le bayésien, comme en phase 5b. Changer la règle des cotations n'y change rien.

## Et ensuite

La prochaine étape sera de réentraîner la v3 sur ce marché, avec la règle du site et des Hard simulés à la table, de corriger la lecture du marché en début de manche, et de mesurer chaque changement à la fois au rejeu des vraies manches et en tournoi. Je proposerai un plan précis avant de commencer.

## Limites

Le Hard simulé est réglé sur 60 manches, toutes jouées contre le bot de Rasmus, à une seule table. Ces journaux contiennent donc aussi sa façon de jouer, et ne disent rien des tables à 5 joueurs ni des autres niveaux de bots du site. Il reste aussi des écarts nets avec les vrais bots, décrits à l'étape 2.

Le rejeu sur le papier ne compte pas la majorité, sert toutes les prises, et ne fait pas réagir le marché. Ses scores servent à comparer des bots, rien de plus.

Tout reste mesuré contre des bots : des bots simulés, ou les vrais bots du site rejoués sur le papier. Rien ici ne mesure le niveau face à des humains, ni ce que mes bots gagneraient vraiment sur figgie.com.

## Reproduire

```bash
cd projets/bot-figgie
python3 -m unittest                                                  # les 113 tests, environ 15 s
python3 -m figgie.calibrate --settings 3000 --rounds 30 --keep 10 --out calibration_hard.json
python3 -m figgie.reel --stats --paper marginal adaptatif_v3 lecteur bayesien heuristique hard_simule --calibration
python3 -m figgie.tournoi --site --candidates marginal adaptatif_v2 adaptatif_v3 --rounds 10 --deals 300 --no-tables \
    --opponents hard_simule heuristique sniper bayesien marginal \
    --references hard_simule heuristique sniper bayesien marginal exploiteur exploiteur_lecteur --out tournoi_site.json
```

La recherche de réglages prend environ 7 minutes sur 10 cœurs, le rejeu des vraies manches 10 secondes. Pour revenir exactement au code de cette phase : `git checkout phase5c-figgie`.
