# Phase 5e : deux questions laissées par la 5d

*English version: [phase5e.en.md](phase5e.en.md)*

La phase 5d m'a laissé deux questions. Sur les vraies manches de figgie.com rejouées sur le papier, le bayésien gagnait 13,5 $ de plus par manche que la v4, alors que tous mes bots le battent largement en simulation. Pourquoi ? Et pourquoi la v4 gagnait-elle deux fois moins que la v3 face au sniper ?

Cette phase répond aux deux. La première avance venait du score du rejeu, qui ne comptait pas la majorité. Avec une majorité estimée, le bayésien tombe au fond du classement et la v4 passe en tête. La seconde venait d'un trou dans l'entraînement de la v4 : elle n'avait jamais vu de table où personne ne cote. Je l'ai bouché, ce qui donne la v4b.

Au tournoi, la v4b gagne deux fois plus que la v4 face au sniper (+27,32 $ par manche contre +13,11) et fait jeu égal avec elle partout ailleurs. Elle échoue toujours au test de minorité, face aux trois mêmes joueurs qu'en phase 5d. Aucun bot n'est promu.

## Étape 1 : le bayésien et la majorité

### Le problème

Le rejeu sur le papier met mon bot à la place de celui de Rasmus, avec sa vraie donne, et le laisse prendre les vraies cotations des bots du site. Jusqu'ici, son score comptait l'argent des prises et 10 $ par carte objectif de plus à la cloche. Il ne comptait pas la majorité, faute de connaître les mains des bots du site.

Or la majorité vaut 100 ou 120 $ à 4 joueurs. Le bayésien estime une carte objectif à environ 10 $ fois la probabilité que ce soit la bonne couleur : il ne compte pas la majorité non plus. C'est presque exactement la règle du score. Je soupçonnais donc que le score l'avantageait.

### Estimer la majorité

Les journaux de Rasmus contiennent deux choses dont je ne m'étais pas servi : le vrai gain de son bot à chaque manche, majorité comprise, et sa main à la cloche. En retirant la mise, l'argent de ses échanges et 10 $ par carte objectif, j'obtiens sa vraie part de majorité. Elle tombe juste dans les 60 manches : 0 $, 100 ou 120 $ quand il a gagné la majorité seul, 50 ou 60 $ quand il l'a partagée.

Je ne connais toujours pas les mains des bots du site, mais je peux en tirer de possibles. Je tire le paquet selon la donne de Rasmus, puis les mains des trois autres. Je ne garde que les tirages où chaque vente du journal porte sur une carte que le vendeur avait, et où Rasmus touche bien sa vraie part de majorité. Il faut entre quelques centaines et quelques dizaines de milliers de tirages pour en garder 200 par manche.

Je rejoue ensuite la manche sur le papier comme avant, en suivant les cartes objectif que mes prises ont fait changer de main. Pour chaque main possible, je recalcule la part de majorité de mon bot. Le nouveau score est l'ancien, plus la part moyenne sur les 200 mains, moins la vraie part de Rasmus. Les mains tirées sont les mêmes pour tous les bots.

Le test de cette étape est une manche écrite à la main. Rasmus garde ses 5 cœurs et partage la majorité (50 $). Mon bot achète 4 cœurs au siège 1. Avec 9 cœurs, le paquet en compte forcément 10 et personne d'autre ne peut en avoir plus d'un : il a la majorité seul, qui vaut 100 $. J'ai aussi vérifié à la main qu'un bot qui ne fait rien obtient exactement 0 sur les 60 vraies manches.

### Le résultat

Score par manche sur les 60 vraies manches, compté par rapport à ce que le bot de Rasmus a vraiment gagné (environ +60 $ par manche) :

| Bot | Sans la majorité | Avec la majorité estimée | Part de la majorité |
|---|---|---|---|
| adaptatif v4 | -4,57 | **-18,72** [-31,15 ; -6,28] | -14,15 |
| lecteur du site | -15,72 | -32,49 | -16,77 |
| exploiteur | **+17,27** | -41,20 | -58,47 |
| adaptatif v3 | -18,83 | -43,35 | -24,52 |
| marginal | -26,37 | -48,67 | -22,30 |
| bayésien | +8,97 | -55,20 | -64,17 |

J'ai refait le calcul avec deux autres graines, qui changent le tirage des mains et le hasard des bots. Les scores bougent d'au plus 3 $ par manche, et le classement ne change pas.

Avec la majorité, le classement s'inverse. Le bayésien perd 64 $ de majorité par manche et passe de la deuxième place à la dernière. La v4 devient la meilleure, de 36,48 $ par manche [+19,23 ; +53,73] devant le bayésien, de 24,63 $ [+9,81 ; +39,45] devant la v3, et de 22,48 $ [+5,95 ; +39,02] devant l'exploiteur. Ces écarts sont appariés, manche par manche.

En décomposant les prises du bayésien, on voit d'où vient sa perte. Il vend en moyenne 4,8 cartes objectif par manche, au prix que proposent les bots du site, parce que pour lui une carte objectif ne vaut que 10 $. Sans la majorité, ces ventes lui rapportaient. Avec elle, elles font souvent passer la majorité à un autre joueur. La v4, qui compte la majorité comme le marginal, ne vend que 2,4 cartes objectif par manche.

J'en tire deux choses. Le rejeu sans la majorité classait mal les bots, et c'est sur lui que reposait l'avance du bayésien en phases 5c et 5d. Et tous mes bots restent loin derrière le bot de Rasmus sur ses propres manches.

Le plan prévoyait de construire un candidat inspiré du bayésien s'il gardait son avance. Il ne la garde pas, donc je ne l'ai pas fait.

## Étape 2 : la v4 face au sniper

### La cause

J'ai joué chaque réglage fixe face à trois snipers, sur 40 donnes du tournoi et en parties de 10 manches, avec la règle du site :

| Réglage (écart, marge → en fin de manche) | joué par le marginal | joué par le lecteur du site |
|---|---|---|
| 6,3 | +17,00 | +17,59 |
| 8,1 | +15,24 | +15,95 |
| 10,3 | +13,18 | +12,53 |
| 12,3 | +11,30 | +9,92 |
| 8,1 → 3,1 | +23,56 | +25,91 |
| 12,3 → 4,1 | +27,16 | **+28,50** |

Face aux snipers, il faut un écart large qui se resserre en fin de manche. La v3 choisit toujours 12,3 → 4,1 et gagne +26,24. La v4 choisit toujours 10,3 et ne gagne que +12,75.

La raison tient au profil de table. Un sniper ne cote jamais : à une table de snipers, 100 % des adversaires sont muets. Aucune des tables d'entraînement de la v4 n'était entièrement muette, et les plus proches n'en avaient qu'un sur trois. La v4 extrapole donc, et ses cinq plus proches voisins viennent tous d'une même table d'entraînement, où le meilleur réglage était 10,3. La v3 n'en avait pas vu non plus, mais ses voisins les plus proches lui donnaient le bon réglage, par chance.

### Le correctif : la v4b

Le test que j'avais prévu pour cette étape (« la v4 ne choisit pas les mêmes réglages face aux snipers et face aux Hard simulés ») passait déjà sans rien changer : elle choisit 6,3 face aux Hard simulés. Il ne mesurait donc rien. Je l'ai remplacé avant d'écrire le correctif, par celui-ci : à une table de snipers, la v4b doit choisir l'un des deux réglages qui se resserrent en fin de manche. La v4 y échoue.

La v4b est la v4 avec 24 tables d'entraînement de plus : des tables « pleines », où tous les adversaires sont des copies d'un même bot de la ligue (les 11 bots de la ligue et le Hard simulé, à 4 puis à 5 joueurs). Elles sont jouées comme celles de la v4, sur des donnes que l'entraînement de la v4 n'a jamais utilisées. J'ai ajouté leurs lignes au modèle du tour 2, sans réentraîner le reste. La construction a pris 11 minutes sur 10 cœurs.

Face aux snipers, la v4b choisit maintenant 12,3 → 4,1. Ses choix bougent aussi à d'autres tables pleines, celles de l'agressif, du passif et de l'aléatoire. Aux tables façon test de minorité, ils bougent peu. En validation croisée sur toutes les tables, choisir le réglage rapporte +4,52 $ par manche [+3,67 ; +5,38] de plus que le réglage fixe.

Sur les vraies manches, la v4b fait jeu égal avec la v4 : +0,78 $ par manche [-1,81 ; +3,38] sans la majorité, +2,63 [-1,94 ; +7,20] avec.

## Étape 3 : le tournoi

J'ai rejoué le tournoi de la phase 5d, sur les mêmes 300 donnes (graine 1), avec la règle du site et en parties de 10 manches. Le candidat est la v4b. J'ai ajouté la v4 aux adversaires et aux références, pour avoir le duel dans les deux sens. Les chiffres de la v4 viennent du tournoi de la phase 5d, joué sur les mêmes donnes. Le tournoi a pris 4 h 10 sur 10 cœurs.

### Contre des tables de copies

Gain moyen par manche, en dollars, de chaque bot face à des copies de l'adversaire. Tous les IC à 95 % font au plus ±1,1 $.

| Adversaire | v4, 4 j. | v4b, 4 j. | v4, 5 j. | v4b, 5 j. |
|---|---|---|---|---|
| Hard simulé | +35,81 | +35,77 | +34,41 | +34,51 |
| heuristique | +43,00 | +43,13 | +45,62 | +44,51 |
| sniper | +13,11 | **+27,32** | +11,48 | **+25,76** |
| bayésien | +25,42 | +26,57 | +27,36 | +27,81 |
| marginal | +8,29 | +8,46 | +4,91 | +4,94 |
| v3 | -1,02 | -0,95 | +0,17 | -0,06 |
| v4 | | -0,15 | | +0,08 |

Face au sniper, la v4b gagne 14 $ de plus par manche que la v4, à 4 comme à 5 joueurs : +27,32 [+26,53 ; +28,11] contre +13,11 [+12,46 ; +13,76]. Elle fait mieux que la v3 (+26,07), qui détenait jusqu'ici le meilleur score face au sniper. Partout ailleurs, les deux versions sont à moins de 1,2 $ l'une de l'autre. Face à face, elles font jeu égal : -0,15 [-0,42 ; +0,13] à 4 joueurs.

### Le test de minorité

Gain d'une référence seule face aux copies du bot. Un nombre positif dont l'intervalle ne touche pas 0 veut dire que le bot se fait exploiter quand il est nombreux à la table.

| Référence seule | v4, 4 j. | v4b, 4 j. | v4, 5 j. | v4b, 5 j. |
|---|---|---|---|---|
| Hard simulé | -14,25 | -14,03 | -11,45 | -10,71 |
| heuristique | -26,66 | -26,82 | -26,83 | -26,78 |
| sniper | -3,26 | -3,23 | -2,79 | -2,75 |
| bayésien | -2,01 | -2,13 | -0,52 | -0,39 |
| marginal | -0,73 | -1,02 | **+0,91** | **+0,92** |
| v3 | **+1,05** | **+1,00** | **+2,87** | **+3,01** |
| v4 | | -0,25 | | +0,10 |
| exploiteur | **+3,93** | **+4,05** | **+5,78** | **+5,85** |
| exploiteur lecteur | -4,53 | -4,72 | -2,08 | -1,29 |

En gras, les gains dont l'intervalle est entièrement au-dessus de 0. Pour la v4b : exploiteur +4,05 [+3,58 ; +4,52] et +5,85 [+5,53 ; +6,17], v3 +1,00 [+0,48 ; +1,53] et +3,01 [+2,47 ; +3,54], marginal à 5 joueurs +0,92 [+0,41 ; +1,44].

Le test de minorité ne bouge pas : les mêmes trois joueurs exploitent la v4b, des mêmes montants à quelques centimes près. Le correctif visait les tables de snipers, et c'est tout ce qu'il a changé. La v4b ne passe donc pas la règle d'entrée, et le marginal reste la référence.

### Comparé à la phase 5d

| | v4 (phase 5d) | v4b (phase 5e) |
|---|---|---|
| contre le sniper, 4 j. / 5 j. | +13,11 / +11,48 | **+27,32 / +25,76** |
| contre le Hard simulé, 4 j. / 5 j. | +35,81 / +34,41 | +35,77 / +34,51 |
| rejeu des vraies manches, avec la majorité | -18,72 | -16,09 (écart +2,63 [-1,94 ; +7,20]) |
| exploiteur seul, 4 j. / 5 j. | +3,93 / +5,78 | +4,05 / +5,85 |
| exploitée par | exploiteur, v3, marginal (5 j.) | exploiteur, v3, marginal (5 j.) |

Le bot s'améliore face au sniper, là où le correctif visait, et seulement là. Sur les vraies manches, l'écart avec la v4 est trop petit pour être mesuré. Il ne s'améliore pas au test de minorité. Ces gains sont mesurés contre des bots simulés, ou contre de vrais bots rejoués sur le papier sans que le marché réagisse : ce ne sont pas des gains réels.

## Ce que j'en retiens

La leçon la plus utile de cette phase porte sur la mesure. Pendant deux phases, j'ai cru que le bayésien faisait quelque chose de mieux que mes bots face aux vrais bots du site. En réalité, le score du rejeu oubliait la majorité, et le bayésien est justement le bot qui l'oublie aussi. Un score qui laisse de côté une partie du jeu favorise les bots qui la laissent de côté.

La deuxième leçon porte sur les plus proches voisins. Ils ne savent pas dire qu'une table ne ressemble à rien de ce qu'ils ont vu : ils répondent quand même, avec les voisins les moins lointains. Une seule mesure jamais vue à l'entraînement, la part d'adversaires muets à 100 %, coûtait 14 $ par manche face au sniper. Couvrir les tables extrêmes compte plus que multiplier les tables ordinaires.

Le test de minorité reste le mur, sans changement depuis la phase 5d.

## Et ensuite

Le test de minorité est la question qui reste. Depuis la phase 4, l'exploiteur gagne face aux copies de chacun de mes bots, et la v3 comme le marginal gagnent face aux copies de la v4b. Avant de proposer la suite, je veux savoir si un réglage fixe lui résiste, ou si le problème vient d'ailleurs. Je proposerai un plan précis avant de commencer.

## Limites

La majorité estimée repose sur des mains tirées au hasard parmi celles qui expliquent le journal. Je ne vérifie qu'à la cloche que les bots du site avaient bien les cartes que mon bot leur prend sur le papier, pas au fil de la manche. L'estimation est donc un peu optimiste pour un bot qui achète beaucoup de cartes objectif. Le rejeu ne fait toujours pas réagir le marché, et sert toutes les prises.

La v4b corrige un trou précis de l'entraînement, les tables où personne ne cote. D'autres tables que la v4 n'a jamais vues peuvent la tromper de la même façon.

Les vraies manches viennent d'une seule table, contre le bot de Rasmus. Tout reste mesuré contre des bots, simulés ou rejoués sur le papier. Ces gains ne sont pas des gains réels sur figgie.com.

## Reproduire

```bash
cd projets/bot-figgie
python3 -m unittest                                                  # les 117 tests, environ 5 s
python3 -m figgie.reel --paper bayesien adaptatif_v4 adaptatif_v3 lecteur_site lecteur marginal sniper hard_simule \
    heuristique exploiteur --majority
python3 -m figgie.adapt --v4b resultats/phase5d/entrainement_v4_2.json --previous adaptatif_v3 adaptatif_v4_1 \
    --tables 24 --deals 40 --rounds 3 --arms 6,3,6,3 8,1,8,1 10,3,10,3 12,3,12,3 8,1,3,1 12,3,4,1 \
    --report entrainement_v4b.json
python3 -m figgie.tournoi --site --candidates adaptatif_v4b --rounds 10 --deals 300 --no-tables \
    --opponents hard_simule heuristique sniper bayesien marginal adaptatif_v3 adaptatif_v4 \
    --references hard_simule heuristique sniper bayesien marginal adaptatif_v3 adaptatif_v4 exploiteur exploiteur_lecteur \
    --out tournoi_site.json
```

La construction de la v4b prend 11 minutes sur 10 cœurs, le rejeu des vraies manches avec la majorité une vingtaine de secondes, le tournoi un peu plus de 4 heures. Pour revenir exactement au code de cette phase : `git checkout phase5e-figgie`.
