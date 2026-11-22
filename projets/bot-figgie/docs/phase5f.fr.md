# Phase 5f : le test de minorité

*English version: [phase5f.en.md](phase5f.en.md)*

Depuis la phase 4, aucun de mes bots ne passe le test de minorité. Un joueur seul face à ses copies gagne de l'argent, ce qui veut dire que le bot se fait exploiter quand il est nombreux à la table. En phase 5e, trois joueurs exploitaient la v4b : l'exploiteur de la phase 4 (+4,05 $ par manche à 4 joueurs, +5,85 à 5), la v3 (+1,00 et +3,01) et le marginal à 5 joueurs (+0,92). Cette phase cherche pourquoi, et essaie de corriger.

Le diagnostic trouve une cause. Une copie qui achète ses cartes à l'exploiteur y gagne, mais l'ensemble des copies y perd, et mon entraînement ne jugeait chaque réglage qu'au gain d'une seule copie. J'ai donc entraîné une v4c sur des tables jugées au gain moyen des copies.

Au tournoi, l'exploiteur ne prend plus à ses copies que 3,15 $ par manche à 4 joueurs et 4,65 $ à 5, contre 4,05 et 5,85 $ à la v4b. La v3 à 5 joueurs passe de 3,01 à 2,46 $. Mais les mêmes trois joueurs l'exploitent toujours, la v4b aussi à 5 joueurs (de justesse), et elle gagne un peu moins face au marginal. Aucun bot n'est promu.

## Étape 0 : trois diagnostics

### Aucun réglage fixe ne tient tout le monde

J'ai d'abord joué chaque réglage fixe face à chaque référence : la référence seule, toutes les autres places tenues par le lecteur du site avec ce réglage. J'ai pris les 6 réglages de la v4b, puis 4 autres pour voir si l'un d'eux faisait mieux. Gain de la référence seule, en dollars par manche (200 donnes pour les 6 premiers réglages, 150 pour les 4 autres) :

| Réglage | exploiteur, 4 j. | exploiteur, 5 j. | v3, 4 j. | v3, 5 j. | marginal, 5 j. | sniper, 4 j. |
|---|---|---|---|---|---|---|
| 6,3 | **-1,22** | **-0,77** | +0,37 | +1,67 | +1,40 | +1,60 |
| 8,1 | +2,65 | +4,51 | +4,70 | +5,01 | +0,58 | -4,34 |
| 10,3 | +0,81 | +2,83 | +3,04 | +7,55 | +2,58 | -5,73 |
| 12,3 | +1,60 | +3,43 | +6,54 | +11,97 | +5,49 | -6,23 |
| 8,1 → 3,1 | +4,47 | +6,27 | +1,10 | +3,44 | +1,56 | -2,63 |
| 12,3 → 4,1 | +4,25 | +6,18 | +3,64 | +7,43 | +3,19 | -8,61 |
| 4,3 | +2,45 | +1,40 | +5,38 | +3,41 | +3,61 | +10,03 |
| 6,5 | **-1,54** | **-0,72** | +1,16 | +4,12 | +4,11 | +2,18 |
| 6,3 → 3,1 | +1,05 | +1,68 | +0,61 | +2,27 | +1,92 | +3,08 |
| 4,1 | +3,25 | +2,22 | +4,35 | +3,12 | +2,18 | +9,79 |

Les réglages serrés (6,3 et 6,5) tiennent l'exploiteur, mais le sniper en profite. Les réglages larges tiennent le sniper, mais l'exploiteur et la v3 en profitent. Surtout, à 5 joueurs, la v3 gagne face à chacun des 10 réglages, au moins +1,67 $ par manche. Choisir le bon réglage ne suffira donc pas à passer le test à 5 joueurs face à la v3.

### Comment l'exploiteur gagne

J'ai ensuite regardé ce que fait l'exploiteur seul face à 3 copies de la v4b, sur 100 parties de 10 manches, et je l'ai comparé à une v4b placée au même siège, sur les mêmes donnes.

L'exploiteur ne fait presque que vendre : 3,9 cartes par manche, dont une carte objectif, à 9,5 $ en moyenne pour les autres couleurs et 10,8 $ pour la couleur objectif. Il n'achète presque rien (0,07 carte par manche). Il en tire 38 $ d'argent, perd 10 $ de cartes objectif vendues, et renonce à la majorité : il en touche 3 $ par manche, contre 25 $ pour une v4b à sa place. Au total, il gagne +4,09 $ par manche, contre -1,55 $ pour la v4b.

Les copies, elles, choisissent 8,1 → 3,1 dans 91 % des manches. C'est le réglage qui rapporte le plus à l'exploiteur dans le tableau plus haut (+4,47 $). Si toutes les copies jouaient 6,3, il perdrait 1,22 $.

### Pourquoi l'entraînement ne le voit pas

Le plus surprenant vient ensuite. J'ai compté, pour chaque carte qu'une copie achète à l'exploiteur, ce qu'elle vaut à la cloche pour cette copie : son gain avec la carte, moins son gain sans elle. En moyenne, une carte achetée à l'exploiteur rapporte +3,75 $ à la copie qui l'achète. Acheter est donc rentable pour chaque copie prise une à une. Ce qu'elle gagne vient surtout de la majorité, qu'elle prend aux autres copies. L'ensemble des copies, lui, perd ce que gagne l'exploiteur.

Or l'entraînement de mes bots adaptatifs juge chaque réglage au gain d'une seule copie. Aux tables qui ressemblent au test de minorité, il récompense donc la copie qui achète à l'exploiteur, alors que le test mesure ce que l'exploiteur prend à l'ensemble des copies.

## Étape 1 : entraîner sur le bon critère

### Les tables symétriques

J'ai ajouté à l'entraînement de la v4b des tables « symétriques ». Un seul bot y joue face à des copies qui ont toutes le même réglage, et chaque réglage est jugé au gain moyen des copies. Les adversaires sont les 11 bots de la ligue, le Hard simulé, la v3 et la v4b, à 4 puis à 5 joueurs. Le reste du modèle ne change pas. J'appelle le résultat la v4c.

Les étiquettes de ces tables sont justes. Aux tables de l'exploiteur, 6,3 est le meilleur réglage pour les copies, à 4 comme à 5 joueurs : +0,20 $ par manche à 4 joueurs, contre -1,85 $ pour 8,1 → 3,1 (moyenne des trois tables).

### Le seam

Le test de cette étape joue une partie de 4 manches, l'exploiteur seul face à 3 copies de la v4c. Après la première manche, toutes les copies doivent jouer 6,3. La v4b y échoue : deux copies passent à 8,1 → 3,1.

La v4c y échoue aussi. Avec 28 tables symétriques (une par adversaire et par nombre de joueurs), deux copies jouent 6,3 tout du long, mais la troisième repasse à 8,1 → 3,1 après une main forte. J'ai cherché pourquoi. Ses cinq plus proches voisins viennent presque tous des anciennes tables façon test de minorité, qui jugent au gain d'une seule copie et recommandent 8,1 → 3,1. Ces anciennes tables donnent 2 100 lignes au modèle, à peine plus que les 1 680 des tables symétriques.

J'ai donc essayé trois choses, sans succès :

- **84 tables symétriques**, trois par adversaire et par nombre de joueurs, sur d'autres donnes. La copie repasse encore à 8,1 → 3,1, avec les mêmes voisins.
- **Retirer les anciennes tables façon minorité.** C'est pire : sur trois donnes, la plupart des copies jouent 8,1 → 3,1.
- **Compter trois fois chaque ligne des tables symétriques** parmi les voisins. Une ou deux copies sur trois passent encore à 8,1 → 3,1. J'ai retiré ce poids.

La cause semble plus profonde que le nombre de lignes : avec 84 tables, les tables symétriques donnent 5 040 lignes, plus du double des anciennes, et la copie se trompe toujours. Le profil d'une seule manche est très bruité : à la même table, l'écart médian qu'une copie observe passe de 8 à 26 $ d'une manche à l'autre. Et en partie, les copies ne jouent pas toutes le même réglage, alors qu'aux tables symétriques, si. Leurs profils tombent donc à côté de ceux de l'entraînement : elles cotent plus souvent, avec des écarts plus serrés.

J'ai gardé la v4c avec 84 tables et sans poids. Le test du seam vérifie maintenant l'échec connu. Il échouera s'il y a une erreur, et aussi le jour où toutes les copies joueront 6,3, pour qu'on le remette à l'endroit.

### Ce que la v4c change au test de minorité

Avant le tournoi, j'ai mesuré la référence seule face aux copies de la v4c et de la v4b, sur 100 donnes d'une autre graine que celle du tournoi :

| Référence seule | v4c, 4 j. | v4b, 4 j. | écart | v4c, 5 j. | v4b, 5 j. | écart |
|---|---|---|---|---|---|---|
| exploiteur | +2,91 | +3,36 | **-0,45** [-0,87 ; -0,04] | +4,86 | +5,93 | **-1,07** [-1,52 ; -0,62] |
| v3 | +0,87 | +1,00 | -0,12 [-1,11 ; +0,87] | +2,72 | +3,70 | **-0,98** [-1,94 ; -0,02] |
| marginal | -0,69 | -0,69 | +0,00 [-0,88 ; +0,88] | +0,77 | +1,65 | **-0,89** [-1,72 ; -0,06] |
| sniper | -4,83 | -3,22 | **-1,61** [-2,21 ; -1,01] | -3,16 | -2,32 | **-0,83** [-1,43 ; -0,24] |

La v4c laisse un peu moins à chaque référence, mais l'exploiteur gagne toujours nettement, et la v3 aussi à 5 joueurs.

## Étape 2 : la v3 et le marginal à 5 joueurs

J'ai comparé la v3, le marginal et une copie de la v4c, chacun au même siège face à 4 copies de la v4c, sur les mêmes 200 donnes. Écarts appariés par manche, par rapport à la copie de la v4c :

| | v3 | marginal |
|---|---|---|
| gain | **+2,22** [+0,45 ; +4,00] | -1,34 [-3,06 ; +0,37] |
| part de majorité | **+2,26** [+0,75 ; +3,77] | **+2,56** [+1,05 ; +4,06] |
| cartes objectif à la cloche | -0,01 [-0,06 ; +0,05] | -0,02 [-0,07 ; +0,04] |
| cartes objectif achetées aux copies | +0,13 [+0,09 ; +0,16] | +0,09 [+0,06 ; +0,13] |
| cartes objectif vendues aux copies | +0,13 [+0,10 ; +0,17] | +0,11 [+0,07 ; +0,15] |

La v3 gagne par la majorité, sans finir avec plus de cartes objectif. Elle en échange un peu plus, dans les deux sens, et gagne la majorité un peu plus souvent. Le marginal prend autant de majorité en plus, mais le perd en argent des échanges. Ce diagnostic ne montre pas de cause assez précise pour un correctif ciblé, donc je n'en ai pas fait.

## Étape 3 : le tournoi

J'ai rejoué le tournoi de la phase 5e, sur les mêmes 300 donnes (graine 1), avec la règle du site et en parties de 10 manches. Le candidat est la v4c. La v4b remplace la v4 parmi les adversaires et les références. Les chiffres de la v4b viennent du tournoi de la phase 5e. Le tournoi a pris 4 h 30 sur 10 cœurs.

### Contre des tables de copies

Gain moyen par manche, en dollars, de chaque bot face à des copies de l'adversaire. Tous les IC à 95 % font au plus ±1,1 $.

| Adversaire | v4b, 4 j. | v4c, 4 j. | v4b, 5 j. | v4c, 5 j. |
|---|---|---|---|---|
| Hard simulé | +35,77 | +35,86 | +34,51 | +34,67 |
| heuristique | +43,13 | +43,18 | +44,51 | +44,41 |
| sniper | +27,32 | +27,32 | +25,76 | +25,76 |
| bayésien | +26,57 | +26,74 | +27,81 | +27,79 |
| marginal | +8,46 | +7,75 | +4,94 | +4,59 |
| v3 | -0,95 | -1,03 | -0,06 | -0,02 |
| v4 | -0,15 | | +0,08 | |
| v4b | | +0,13 | | -0,09 |

Les deux versions sont à moins de 0,2 $ l'une de l'autre partout, sauf face au marginal : la v4c y gagne 0,71 $ de moins à 4 joueurs (+7,75 [+7,24 ; +8,25] contre +8,46 [+7,92 ; +9,01]) et 0,35 $ de moins à 5. Face à face, elles font jeu égal : +0,13 [-0,19 ; +0,45] à 4 joueurs, -0,09 [-0,38 ; +0,21] à 5.

### Le test de minorité

Gain d'une référence seule face aux copies du bot. Un nombre positif dont l'intervalle ne touche pas 0 veut dire que le bot se fait exploiter quand il est nombreux à la table.

| Référence seule | v4b, 4 j. | v4c, 4 j. | v4b, 5 j. | v4c, 5 j. |
|---|---|---|---|---|
| Hard simulé | -14,03 | -14,68 | -10,71 | -12,60 |
| heuristique | -26,82 | -26,75 | -26,78 | -26,96 |
| sniper | -3,23 | -4,87 | -2,75 | -3,80 |
| bayésien | -2,13 | -2,54 | -0,39 | -1,20 |
| marginal | -1,02 | -0,80 | **+0,92** | **+0,77** |
| v3 | **+1,00** | **+0,94** | **+3,01** | **+2,46** |
| v4 | -0,25 | | +0,10 | |
| v4b | | +0,16 | | **+0,32** |
| exploiteur | **+4,05** | **+3,15** | **+5,85** | **+4,65** |
| exploiteur lecteur | -4,72 | -5,05 | -1,29 | -1,96 |

En gras, les gains dont l'intervalle est entièrement au-dessus de 0. Pour la v4c : exploiteur +3,15 [+2,69 ; +3,60] et +4,65 [+4,31 ; +4,99], v3 +0,94 [+0,42 ; +1,45] et +2,46 [+1,93 ; +2,99], marginal à 5 joueurs +0,77 [+0,25 ; +1,29], v4b à 5 joueurs +0,32 [+0,00 ; +0,63] (la borne basse vaut +0,002).

Presque toutes les références gagnent moins face aux copies de la v4c que face à celles de la v4b. L'exploiteur perd 0,90 $ par manche à 4 joueurs et 1,20 $ à 5, la v3 à 5 joueurs 0,55 $. C'est cohérent avec la mesure de l'étape 1, faite sur d'autres donnes. Mais l'exploiteur, la v3 et le marginal à 5 joueurs gagnent toujours, et la v4b seule face aux copies de la v4c gagne aussi, de très peu. La v4c ne passe donc pas la règle d'entrée, et le marginal reste la référence.

### Comparé à la phase 5e

| | v4b (phase 5e) | v4c (phase 5f) |
|---|---|---|
| exploiteur seul, 4 j. / 5 j. | +4,05 / +5,85 | **+3,15 / +4,65** |
| v3 seule, 4 j. / 5 j. | +1,00 / +3,01 | +0,94 / +2,46 |
| contre le marginal, 4 j. / 5 j. | +8,46 / +4,94 | +7,75 / +4,59 |
| face à face avec la v4b, 4 j. / 5 j. | | +0,13 / -0,09 |
| exploitée par | exploiteur, v3, marginal (5 j.) | exploiteur, v3, marginal (5 j.), v4b (5 j., de justesse) |

Le bot s'améliore un peu au test de minorité, là où la phase visait, sans le passer. Il ne s'améliore pas ailleurs : il fait jeu égal avec la v4b et gagne un peu moins face au marginal. Les deux tournois utilisent les mêmes donnes, mais je n'ai pas d'écart apparié entre eux : seules les mesures appariées de l'étape 1 donnent un intervalle sur la différence. Ces gains sont mesurés contre des bots simulés : ce ne sont pas des gains réels.

## Ce que j'en retiens

La leçon principale porte sur ce que l'entraînement mesure. Le test de minorité demande si l'ensemble des copies se fait prendre de l'argent. Mon entraînement demandait si une copie en gagnait. Face à l'exploiteur, les deux questions ont des réponses opposées : acheter ses cartes rapporte 3,75 $ à la copie qui achète, et coûte à l'ensemble des copies. Juger au bon critère a réduit ce que l'exploiteur prend, d'environ 1 $ par manche, mais pas assez.

La deuxième leçon porte sur les plus proches voisins. Ajouter des lignes justes ne suffit pas quand les tables du test tombent à côté de celles de l'entraînement. Le profil d'une seule manche est très bruité, et les copies d'un bot adaptatif ne jouent pas toutes le même réglage, alors qu'aux tables symétriques, si.

Enfin, à 5 joueurs, aucun de mes 10 réglages fixes ne tient la v3. Mieux choisir parmi les réglages ne suffira pas : il faudra un autre levier que le spread et la marge.

## Et ensuite

Je vois deux pistes. La première : faire jouer toutes les copies de la même façon, en choisissant le réglage à partir de ce que toutes voient, le marché public, plutôt que de la main de chacune. Elles ressembleraient alors aux tables symétriques de l'entraînement. La seconde : changer de levier, par exemple la façon dont le bot vend ses cartes objectif ou dispute la majorité, puisque le spread et la marge ne tiennent pas la v3 à 5 joueurs. Je proposerai un plan précis avant de commencer.

## Limites

Les diagnostics de l'étape 0 ont été joués sur les 200 premières donnes de la graine du tournoi. Aucun bot n'a été entraîné dessus, mais le choix du critère de l'étape 1 s'appuie sur eux. La mesure de l'étape 1 et le diagnostic de l'étape 2 utilisent une autre graine.

Les adversaires des tables symétriques sont aussi les références du test de minorité. Les donnes diffèrent, mais le tournoi mesure la v4c face à des bots qu'elle a vus à l'entraînement, comme la v4 avant elle.

Aux tables symétriques, les copies jouent un réglage fixe pendant toute la partie. En vrai, les copies de la v4c commencent toutes à 8,1, puis changent de réglage chacune de son côté. L'entraînement ne voit donc jamais exactement la table qu'il prépare.

Tout reste mesuré contre des bots simulés. Ces gains ne sont pas des gains réels sur figgie.com.

## Reproduire

```bash
cd projets/bot-figgie
python3 -m unittest                                                  # les 118 tests, environ 5 s
python3 -m figgie.adapt --v4c resultats/phase5e/entrainement_v4b.json --previous adaptatif_v3 adaptatif_v4_1 \
    --tables 84 --deals 40 --rounds 3 --arms 6,3,6,3 8,1,8,1 10,3,10,3 12,3,12,3 8,1,3,1 12,3,4,1 \
    --report entrainement_v4c.json
python3 -m figgie.tournoi --site --candidates adaptatif_v4c --rounds 10 --deals 300 --no-tables \
    --opponents hard_simule heuristique sniper bayesien marginal adaptatif_v3 adaptatif_v4b \
    --references hard_simule heuristique sniper bayesien marginal adaptatif_v3 adaptatif_v4b exploiteur exploiteur_lecteur \
    --out tournoi_site.json
```

La construction de la v4c prend 51 minutes sur 10 cœurs, le tournoi 4 h 30. Pour revenir exactement au code de cette phase : `git checkout phase5f-figgie`.
