# Phase 5g : des copies qui jouent ensemble, et six nouvelles références

*English version: [phase5g.en.md](phase5g.en.md)*

La phase 5f s'est terminée sur deux pistes. Cette phase essaie la première : faire jouer toutes les copies de la v4c au même réglage, en le choisissant d'après ce que toutes voient. Si les copies ressemblaient aux tables symétriques de l'entraînement, elles choisiraient peut-être 6,3 face à l'exploiteur, le seul réglage qui le tient.

La réponse est non. Faire jouer les copies au même réglage ne réduit pas ce que l'exploiteur leur prend, et une des variantes le laisse gagner davantage. Je n'ai donc pas écrit de v4d sur cette piste.

J'ai profité de la phase pour lire ce qui a été publié sur Figgie depuis mes recherches de la phase 5b : un article et quatre dépôts. J'en ai tiré six nouvelles références pour le test de minorité, toutes réécrites d'après leur description, et une idée de jeu : se taire pendant la première minute. Aucune des six ne gagne d'argent face aux copies de mes bots, et se taire la première minute fait perdre environ 8 $ par manche contre le marginal. Aucun bot n'est promu. Un dernier diagnostic ouvre une piste pour la suite : décrire la table par la moyenne de plusieurs manches réduit ce que l'exploiteur prend aux copies.

## Étape 0 : des copies cohérentes

### Trois variantes

J'ai écrit trois variantes de la v4c, qui ne diffèrent que par la façon de choisir le réglage de la manche suivante :

- **public** : chaque copie décrit la table d'après tout le marché, sans s'exclure elle-même, et consulte ses voisins pour une main forte comme pour une main faible. Toutes les copies voient le même marché, donc elles devraient choisir pareil.
- **partage** : la première copie choisit comme la v4c, et les autres prennent son choix. C'est une triche, puisque les copies se parlent, mais elle répond à la question : si elles jouaient toutes pareil, est-ce que ça aiderait ?
- **sièges** : chaque copie décrit la table depuis chaque siège, et consulte ses voisins pour tous ces profils à la fois.

### Ce qu'elles choisissent face à l'exploiteur

J'ai rejoué le test de la phase 5f : l'exploiteur seul face à 3 copies, une partie de 4 manches, sur trois donnes. Cela fait 27 choix par variante (3 donnes, 3 copies, 3 manches après la première) :

| Variante | 6,3 | 8,1 → 3,1 | autre |
|---|---|---|---|
| v4c | 11 | 15 | 1 |
| public | 3 | 24 | 0 |
| partage | 15 | 12 | 0 |
| sièges | 0 | 27 | 0 |

Rendre les copies cohérentes ne les fait pas choisir le bon réglage. Les variantes public et sièges s'accordent, mais sur 8,1 → 3,1, le réglage qui rapporte le plus à l'exploiteur. Partage choisit 6,3 un peu plus souvent que la v4c, mais pas toujours.

J'ai regardé d'où viennent les voisins des copies de la variante sièges. Ils sont éparpillés sur une vingtaine de tables d'entraînement différentes. En moyenne, ces voisins donnent 4,25 $ par manche à 8,1 → 3,1, contre 3,37 $ à 6,3. Ils recommandent donc 8,1 → 3,1. Le profil d'une manche ne reconnaît pas la table de l'exploiteur, et toutes les copies se trompent ensemble.

### Ce que ça donne au test de minorité

J'ai mesuré la référence seule face aux copies de chaque variante, sur 100 donnes de la graine 7 (pas celle du tournoi). Gain de la référence en dollars par manche, et entre crochets l'écart apparié avec la v4c. Un écart négatif est bon pour mes copies.

| Référence seule | v4c, 4 j. | partage | sièges | v4c, 5 j. | partage | sièges |
|---|---|---|---|---|---|---|
| exploiteur | +2,91 | -0,44 [-0,96 ; +0,08] | **+0,57** [+0,09 ; +1,05] | +4,86 | -0,00 [-0,43 ; +0,43] | **+0,96** [+0,50 ; +1,42] |
| v3 | +0,87 | +0,26 [-0,73 ; +1,26] | +0,25 [-0,73 ; +1,24] | +2,72 | **+1,04** [+0,09 ; +1,98] | **+1,14** [+0,16 ; +2,11] |
| marginal | -0,69 | -0,19 [-1,17 ; +0,79] | -0,08 [-0,96 ; +0,80] | +0,77 | +0,24 [-0,61 ; +1,10] | +0,95 [-0,07 ; +1,97] |
| sniper | -4,83 | **-1,14** [-1,75 ; -0,53] | **-3,71** [-4,32 ; -3,09] | -3,16 | **-1,23** [-1,79 ; -0,68] | -0,45 [-1,07 ; +0,18] |

En gras, les écarts dont l'intervalle ne touche pas 0. Face à l'exploiteur, partage ne fait pas mieux que la v4c, et sièges fait pire. Face à la v3 à 5 joueurs, les deux font pire. Le seul gain net est face au sniper, qui perdait déjà face à la v4c.

Mon plan prévoyait d'écrire une v4d seulement si ce diagnostic montrait un effet. Il n'en montre pas, donc je me suis arrêté là. Les variantes sont restées des scripts de diagnostic, hors du dépôt.

## Étape 1 : ce que d'autres ont publié

### Ce que j'ai lu

| Source | Ce que c'est | Licence | Ce que j'en ai repris |
|---|---|---|---|
| DiSilvio, Luo et Ozerov, « Traders in a Strange Land » (arXiv 2110.00879, 2021) | une simulation de Figgie à 4 joueurs, avec des agents écrits à la main | CC BY 4.0 | l'imitateur, le fondamentaliste, l'idée de la v4c calme, le bootstrap |
| LSeaburg/FiggieServer | un serveur qui imite le site, avec les agents de l'article | aucune | deux règles du site à vérifier, la valeur r = 1,7 |
| CornellDataScience/FiggieBot (2022) | un serveur et un agent de comptage inachevé | aucune | la valeur r = 3,5 |
| 0xDub/figgie-auto, et son fork Pranay0302/figgie | un moteur en Rust avec 7 stratégies, puis un transformeur entraîné dessus | aucune | trois stratégies, réécrites |
| parmarsuraj99/figgie-python-rl (2024) | un serveur et des agents LLM | aucune | rien |

Sans licence, je n'ai repris aucun code, seulement des idées décrites en mots. Plusieurs de ces projets s'éloignent des règles sur des points qui comptent. Chez Cornell, dans figgie-auto et dans figgie-python-rl, la couleur objectif a 8 cartes une fois sur 2 ou une fois sur 4, au lieu d'une fois sur 3. figgie-python-rl ne verse même pas la majorité. Le transformeur de Pranay0302 annonce 75 % de victoires, mais c'est la part des manches où il gagne quelque chose, sans intervalle ni donnes dupliquées, sur des manches de 30 s et face à des adversaires que son propre README dit cassés (trois copies d'un même bot y partagent un seul inventaire). Je ne m'en sers donc pas comme point de comparaison.

### L'imitateur

Parmi les agents de l'article, il y a un « bottom feeder », que j'appelle l'imitateur. Il ne cherche pas la couleur objectif. Il regarde les prix auxquels les autres joueurs proposent d'acheter et de vendre, en fait une moyenne, puis propose d'acheter moins cher que cette valeur ou de vendre plus cher. Il vit des prix des autres, ce qui en fait un candidat naturel pour le test de minorité.

Je l'ai réécrit d'après l'article. Il regarde le marché toutes les 2 secondes en moyenne, choisit au hasard une couleur et un côté, et tire un prix entre 1 $ et sa valeur pour acheter, ou entre sa valeur et le double pour vendre. Si ce prix atteint la meilleure offre d'en face, il la prend. Deux différences avec l'article : celui-ci attend 4 prix de chaque côté avant d'agir, et l'imitateur y suit une proie choisie à la main. Sur nos tables, il n'agirait presque jamais, donc je prends les 4 derniers prix dès qu'il y en a un de chaque côté, et ses proies sont tous les autres joueurs. Le test du seam vérifie qu'il n'achète jamais au-dessus de sa valeur et ne vend jamais en dessous.

### Les fondamentalistes

Dans l'article, le fondamentaliste est la stratégie la plus rentable dans toutes les combinaisons testées. Il pèse chacun des 12 paquets possibles par le nombre de façons d'y trouver les cartes qu'il a vues : sa main et les cartes passées de main en main dans les échanges. Une carte d'une couleur vaut ensuite, pour chaque paquet où cette couleur est l'objectif, 10 $ plus une part géométrique de la majorité : p (1 − r) r^h / (1 − r^x), où h est son nombre de cartes de la couleur, x la majorité sûre (5 cartes si l'objectif en a 8, 6 sinon) et p ce qui reste du pot (120 ou 100 $). Vendre une carte vaut la même chose avec h − 1. Il cote comme l'imitateur.

L'article ne donne pas de valeur pour r, seulement r > 1. J'en ai pris deux : 1,7, comme FiggieServer, et 3,5, comme le dépôt de Cornell. Le test du seam vérifie sa valeur sur un exemple calculé à la main : avec la main S4 C1 H3 D2 et sans échange, un cœur vaut 5,93 $ à l'achat et 4,32 $ à la vente.

L'article insiste sur un point : retirer les offres que la nouvelle valeur ne justifie plus. Je ne le fais pas. Avec la règle du site, sa valeur ne change qu'après un échange, qui vide déjà le carnet.

Un détail m'a frappé en relisant l'article. Le fondamentaliste compte toutes les cartes vues comme si elles avaient été tirées au hasard. Or une carte achetée a été choisie : compter ainsi rend le bot trop sûr de lui. C'est exactement le calcul de ma phase 2, que j'ai corrigé en phase 3. Je l'ai gardé tel quel, puisque c'est l'agent de l'article que je veux mesurer.

### Trois stratégies de figgie-auto

figgie-auto décrit 7 stratégies. Je n'en ai pas réécrit quatre : Noisy ressemble à mon aléatoire, PickOff à mon sniper, Spread est un teneur de marché naïf, et TheHoarder, qui veut 6 cartes de chaque couleur, est décrit par son auteur lui-même comme risqué et peu rentable. J'ai réécrit les trois autres :

- **le vendeur** (« Seller ») ne fait que vendre. Il propose chaque couleur qu'il a à un prix plancher qui baisse avec le temps (8 $ la première minute, puis 6, 6 et 4 $), et prend les offres d'achat assez hautes. Il ressemble à mon exploiteur, qui gagne justement en vendant.
- **la mante** (« PrayingMantis ») vend tout pendant 3 minutes, 1 $ sous l'offre de vente affichée si elle vaut 7 $ ou plus. Dans la dernière minute, elle achète à 9 $ au plus la couleur dont le dernier échange a été le plus cher. Sur le site, presque la moitié des échanges tombent dans la dernière minute.
- **le parieur** (« TiltInventory ») parie sur la couleur dont il avait le plus de cartes au départ. Il l'achète jusqu'à 8 $ et vend les autres.

Les trois regardent le marché toutes les 2 à 4 s, comme dans figgie-auto, et ne cotent que pour battre l'offre affichée. Une différence : là-bas, ils envoient tous leurs ordres d'un coup, ici une seule action tirée au hasard à chaque fois. Chacun a son test de seam.

### Au tournoi

J'ai mis les cinq nouvelles références au test de minorité, seules face aux copies de la v4c, de la v4b et du marginal, sur les 300 donnes du tournoi (graine 1), avec la règle du site et en parties de 10 manches. Chaque chiffre est le gain moyen de la référence par manche, avec son intervalle à 95 %.

| Référence seule face à | v4c 4 j. | v4c 5 j. | v4b 4 j. | v4b 5 j. | marginal 4 j. | marginal 5 j. |
|---|---|---|---|---|---|---|
| fondamentaliste (r = 1,7) | -10,93 [-11,71 ; -10,14] | -6,88 [-7,56 ; -6,20] | -11,01 [-11,77 ; -10,24] | -7,25 [-7,91 ; -6,59] | -8,10 [-8,85 ; -7,36] | -7,03 [-7,71 ; -6,36] |
| fondamentaliste (r = 3,5) | -14,63 [-15,34 ; -13,91] | -11,23 [-11,79 ; -10,67] | -14,29 [-15,02 ; -13,56] | -11,53 [-12,05 ; -11,01] | -11,68 [-12,37 ; -10,99] | -11,00 [-11,52 ; -10,48] |
| vendeur | -6,65 [-7,06 ; -6,24] | -2,49 [-2,79 ; -2,18] | -5,94 [-6,35 ; -5,53] | -1,42 [-1,72 ; -1,12] | -5,73 [-6,17 ; -5,30] | -4,53 [-4,85 ; -4,21] |
| mante | -7,95 [-8,38 ; -7,53] | -5,63 [-5,98 ; -5,28] | -6,51 [-6,92 ; -6,11] | -3,95 [-4,33 ; -3,58] | -11,85 [-12,25 ; -11,44] | -9,49 [-9,81 ; -9,18] |
| parieur | -5,82 [-6,32 ; -5,32] | -3,08 [-3,52 ; -2,65] | -4,12 [-4,61 ; -3,62] | -1,71 [-2,21 ; -1,21] | -11,09 [-11,52 ; -10,66] | -9,44 [-9,77 ; -9,11] |

Les 30 cases sont négatives, intervalles compris : aucune des cinq références ne gagne d'argent face aux copies. L'exploiteur reste donc le seul bot connu qui exploite la v4c (+3,15 et +4,65 $). Le plus dangereux des nouveaux est le vendeur, à 5 joueurs, et ce n'est pas un hasard : il gagne comme l'exploiteur, en vendant. Il lui manque seulement de savoir quoi vendre.

Trois choses m'ont surpris. Le fondamentaliste de l'article, le plus rentable là-bas, est ici parmi les pires : il paie sa confiance excessive, et plus r est grand, plus il la paie. La v4c laisse moins que la v4b aux trois stratégies de figgie-auto, de 0,7 à 1,7 $ selon la case, ce que je n'avais pas cherché. Et le marginal punit beaucoup plus fort la mante et le parieur que les bots adaptatifs : de 9 à 12 $ par manche, contre 2 à 8 $. Un bot qui ne s'adapte pas reste donc une bonne défense contre les stratégies fixes.

## Étape 2 : se taire la première minute

L'article mesure une chose que je n'attendais pas (tableau 3). Parmi quatre fondamentalistes identiques, celui qui n'a aucune latence finit avec moins d'argent que les trois lents : face à chacun, l'intervalle à 95 % de l'écart tombe entre 12 et 41 $. Les auteurs l'expliquent ainsi : il échange plus souvent au début, quand ses valeurs bougent encore beaucoup. Ça rejoint ma phase 5d, où le lecteur du site a appris à ne pas croire les offres de la première minute.

J'ai donc essayé la v4c calme : la v4c qui n'envoie aucun ordre pendant les 30 ou les 60 premières secondes de chaque manche, puis joue normalement. Elle lit quand même le marché, donc son choix de réglage ne change pas. Le test du seam le vérifie dans une vraie partie.

Avant de lancer le diagnostic, j'ai fixé la règle de décision. Une variante calme aide si trois conditions sont réunies : l'écart apparié de l'exploiteur a un intervalle entièrement sous 0, à 4 ou à 5 joueurs ; aucune autre référence n'a d'écart entièrement au-dessus de 0 ; et contre le marginal, la borne basse de l'écart reste au-dessus de -1 $. Si une variante aidait, elle passait au tournoi complet.

Je l'ai mesurée comme à l'étape 0, sur 100 donnes de la graine 7, en écarts appariés avec la v4c. Un écart négatif est bon pour mes copies dans les lignes « seul », et mauvais dans la ligne « contre le marginal », où c'est le gain de mon bot.

| | v4c, 4 j. | calme 30 s | calme 60 s | v4c, 5 j. | calme 30 s | calme 60 s |
|---|---|---|---|---|---|---|
| exploiteur seul | +2,91 | +0,31 [-0,25 ; +0,86] | -0,24 [-0,79 ; +0,32] | +4,86 | **+0,55** [+0,10 ; +1,00] | -0,10 [-0,60 ; +0,40] |
| v3 seul | +0,87 | **+2,18** [+1,30 ; +3,07] | +0,39 [-0,67 ; +1,45] | +2,72 | **+2,14** [+1,05 ; +3,22] | **+1,17** [+0,10 ; +2,24] |
| marginal seul | -0,69 | **+2,37** [+1,23 ; +3,50] | **+1,22** [+0,13 ; +2,31] | +0,77 | **+2,00** [+0,99 ; +3,01] | **+1,66** [+0,64 ; +2,68] |
| sniper seul | -4,83 | **+1,12** [+0,38 ; +1,86] | **+1,20** [+0,52 ; +1,89] | -3,16 | **+0,82** [+0,21 ; +1,43] | **+1,81** [+1,13 ; +2,49] |
| fondamentaliste seul | -10,08 | +0,04 [-1,11 ; +1,19] | **-1,15** [-2,23 ; -0,08] | -5,90 | -0,51 [-1,57 ; +0,55] | +0,41 [-0,85 ; +1,68] |
| contre le marginal | +7,94 | **-8,29** [-9,31 ; -7,27] | **-7,59** [-8,70 ; -6,47] | +5,08 | **-7,95** [-8,89 ; -7,02] | **-7,62** [-8,48 ; -6,76] |

Aucune des deux variantes n'aide, et de loin. Se taire ne retire rien à l'exploiteur, dont aucun intervalle ne passe sous 0. Le v3, le marginal et le sniper prennent tous davantage aux copies calmes. Surtout, contre le marginal, mon bot perd environ 8 $ par manche, presque tout ce qu'il gagnait : il passe de +7,94 à -0,34 $ à 4 joueurs, et de +5,08 à -2,88 $ à 5.

Je ne m'attendais pas à un effet aussi fort, et je ne l'ai pas expliqué. Ce que dit le chiffre, c'est que la v4c gagne une bonne part de son argent pendant la première minute, et qu'un concurrent qui s'y tait laisse les meilleures affaires aux autres. Le résultat de l'article ne se transpose donc pas : chez lui, les quatre joueurs étaient des fondamentalistes trop sûrs d'eux, que les échanges précoces trompaient. Les miens comptent correctement les cartes achetées depuis la phase 3.

La v4c calme reste dans le code comme candidate mesurée, mais elle n'est pas promue.

## Étape 3 : décrire la table sur plusieurs manches

La règle fixée avant le diagnostic prévoyait, si aucune variante calme n'aidait, de tester une autre idée tirée de l'étape 0. Le profil d'une seule manche ne reconnaît pas la table de l'exploiteur. Aujourd'hui, la v4c consulte ses voisins manche par manche, puis fait la moyenne de leurs conseils. J'ai essayé l'inverse : faire d'abord la moyenne des profils des manches passées, puis consulter les voisins une seule fois avec ce profil moyen. Une variante prend toutes les manches passées, l'autre les 3 dernières. C'est un script de diagnostic, hors du dépôt.

Au test des 27 choix, rien ne bouge : 12 fois 6,3, contre 11 pour la v4c. Les deux variantes y font les mêmes choix, ce qui est normal sur 4 manches, où il y a au plus 3 profils à moyenner. Le test de minorité, en parties de 10 manches, dit autre chose (100 donnes de la graine 7, écarts appariés avec la v4c) :

| | v4c, 4 j. | toutes les manches | 3 dernières | v4c, 5 j. | toutes les manches | 3 dernières |
|---|---|---|---|---|---|---|
| exploiteur seul | +2,91 | **-0,82** [-1,30 ; -0,34] | **-0,71** [-1,18 ; -0,25] | +4,86 | **-0,62** [-1,02 ; -0,22] | **-0,65** [-1,06 ; -0,24] |
| v3 seul | +0,87 | -0,43 [-1,19 ; +0,34] | -0,13 [-0,86 ; +0,61] | +2,72 | -0,56 [-1,43 ; +0,31] | -0,56 [-1,41 ; +0,30] |
| marginal seul | -0,69 | -0,03 [-0,91 ; +0,85] | -0,18 [-1,05 ; +0,68] | +0,77 | -0,25 [-1,23 ; +0,73] | **-0,93** [-1,83 ; -0,03] |
| sniper seul | -4,83 | -0,35 [-0,94 ; +0,24] | -0,26 [-0,81 ; +0,29] | -3,16 | +0,12 [-0,40 ; +0,64] | -0,08 [-0,57 ; +0,41] |
| fondamentaliste seul | -10,08 | -0,41 [-1,40 ; +0,58] | **-0,93** [-1,83 ; -0,03] | -5,90 | -0,09 [-1,04 ; +0,85] | -0,46 [-1,33 ; +0,41] |
| contre le marginal | +7,94 | -0,69 [-1,42 ; +0,03] | **-1,00** [-1,74 ; -0,26] | +5,08 | -0,36 [-0,89 ; +0,18] | -0,38 [-1,07 ; +0,30] |

C'est la première fois qu'une variante réduit nettement ce que l'exploiteur prend aux copies, à 4 comme à 5 joueurs : de 0,6 à 0,8 $ par manche, soit 28 % de son gain à 4 joueurs et 13 % à 5. Aucune autre référence n'y gagne. Le prix, c'est un peu moins de gain contre le marginal. Si j'appliquais la règle fixée pour la v4c calme, la variante « toutes les manches » échouerait de peu : la borne basse de son écart contre le marginal est à -1,42 $ à 4 joueurs, sous le seuil de -1 $. Et même avec ce gain, l'exploiteur garde +2,09 et +4,24 $ : le test de minorité échouerait toujours.

Je n'en ai pas fait une v4d cette nuit. Ce n'était pas dans le plan validé, et 100 donnes d'une seule graine ne suffisent pas pour promouvoir un bot.

## Deux règles du site

FiggieServer contient deux observations sur le site qui touchent mon moteur.

**Les retraits.** Les bots du site retirent-ils leurs offres ? Dans les journaux de Rasmus Suonio, les bots Hard ont 233 retraits. 97 % tombent à la seconde d'un échange ou la seconde d'après (164 à la même seconde, 63 une seconde après). Ce ne sont pas des retraits volontaires : après un échange, le site vide le carnet de la couleur, et le journal le note comme des retraits. C'est ce que dit l'auteur de FiggieServer. Mon Hard simulé ne retire jamais d'offre, ce qui est cohérent.

**Croiser sa propre offre.** Si un joueur propose d'acheter au prix de sa propre offre de vente, mon moteur refuse l'action, comme FiggieServer. D'après son auteur, le site retire plutôt toutes les offres de ce joueur dans la couleur. Je n'ai pas pu le vérifier dans les journaux. Je pense que l'effet est faible, sans l'avoir mesuré, donc je laisse le moteur tel quel et je le note dans les limites.

## Contrôle : mes intervalles de confiance

Dans un jeu à somme nulle, les gains des joueurs d'une même partie ne sont pas indépendants, et leur distribution a souvent deux bosses : on a deviné la couleur objectif, ou pas. L'article compare donc ses stratégies avec un bootstrap. Mes donnes dupliquées règlent déjà la dépendance, puisque chaque valeur est une donne et que les donnes sont indépendantes. Mais mes intervalles supposent une loi normale, et je ne l'avais jamais vérifié.

J'ai donc recalculé tous les intervalles du diagnostic de l'étape 2 avec un bootstrap par percentiles : 10 000 tirages avec remise des 100 valeurs, et on garde les moyennes à 2,5 % et 97,5 %. Sur les 60 cases, valeurs brutes et écarts appariés, la plus grande différence entre une borne normale et une borne bootstrap est de 0,03 $, soit 1,8 % de la largeur de l'intervalle. Aucune conclusion ne change. Avec 100 donnes ou plus, la moyenne est déjà assez proche d'une loi normale pour que mes intervalles tiennent, malgré les deux bosses.

## Le tournoi

La v4c n'a pas changé depuis la phase 5f, et le moteur est déterministe : rejouer tout le tournoi redonnerait les mêmes chiffres. J'ai donc rejoué seulement ce qui est nouveau, sur les mêmes 300 donnes (graine 1), avec la règle du site, en parties de 10 manches. J'y ai ajouté des contrôles, qui retombent exactement sur les phases précédentes : la v4c fait +7,75 et +4,59 $ contre le marginal, comme en phase 5f, la v4b +8,46 et +4,94 $, comme en phase 5e, et l'exploiteur prend toujours +3,15 et +4,65 $ aux copies de la v4c.

L'imitateur seul face aux copies :

| Imitateur seul face à | 4 j. | 5 j. |
|---|---|---|
| v4c | -27,13 [-28,10 ; -26,16] | -24,24 [-25,32 ; -23,15] |
| v4b | -27,07 [-27,99 ; -26,15] | -24,03 [-25,07 ; -23,00] |

Aucun nouveau candidat n'est entré au tournoi complet, puisque la v4c calme a échoué au diagnostic. La v4c reste donc le meilleur bot, avec les mêmes chiffres qu'en phase 5f, et elle échoue toujours à la règle d'entrée à cause du test de minorité : l'exploiteur lui prend +3,15 et +4,65 $ par manche. Les règles d'entrée affichées dans les fichiers de résultats de cette phase ne portent que sur les adversaires et les références rejoués ici, pas sur tout le zoo. Le bot ne progresse pas dans cette phase.

Tous ces chiffres sont mesurés contre des bots simulés : ce ne sont pas des gains réels.

## Ce que j'en retiens

Je pensais que les copies perdaient parce qu'elles ne jouaient pas toutes pareil. Le diagnostic dit autre chose : elles reconnaissent mal la table. Quand elles s'accordent, c'est sur le mauvais réglage, et elles perdent ensemble. Le problème est en amont, dans le profil d'une seule manche, qui ne distingue pas la table de l'exploiteur des vingt tables d'entraînement qui lui ressemblent.

Les références trouvées ailleurs ne m'ont rien appris de neuf sur mes faiblesses : aucune ne fait mieux que l'exploiteur, qui reste mon pire adversaire. Elles servent quand même : elles élargissent le test de minorité à des styles que je n'aurais pas écrits, et elles montrent que la v4c tient mieux que la v4b face aux trois stratégies de figgie-auto.

La v4c calme m'a appris que la première minute vaut cher. Une idée qui marche chez quelqu'un d'autre ne se transpose pas quand ses bots ne font pas la même erreur que les miens.

Le profil moyen va dans le sens du diagnostic de l'étape 0 : le problème est la reconnaissance de la table, et regarder plusieurs manches à la fois aide un peu.

## Et ensuite

La piste la plus nette est le profil moyen de l'étape 3. Je propose de le mesurer sur plus de donnes, puis, s'il tient, d'en faire une v4d et de la passer au tournoi complet et à la règle d'entrée. Il restera à combler l'écart avec le marginal, et à retirer beaucoup plus à l'exploiteur, qui garderait encore 2 à 4 $ par manche. L'autre piste de la phase 5f reste ouverte : changer de levier, par exemple la façon de vendre les cartes objectif. Je proposerai un plan avant de commencer.

## Limites

Les variantes des étapes 0, 2 et 3 ont été mesurées sur 100 donnes seulement, d'une autre graine que celle du tournoi. La variante public n'a été jouée qu'au test des 27 choix, pas au test de minorité, parce qu'elle choisissait 8,1 → 3,1 encore plus souvent que la v4c.

Les six références sont des réécritures d'après des descriptions. L'imitateur et les fondamentalistes s'écartent de l'article sur les points notés plus haut, et les stratégies de figgie-auto n'y envoient pas leurs ordres de la même façon. Avec la règle du site, une partie de leurs offres est refusée parce qu'elle ne bat pas l'offre affichée. Un refus a le même effet sur le marché que de ne rien faire, mais il coûte son tour au bot. Pour l'imitateur et les fondamentalistes, c'est environ la moitié des ordres (234 sur 475 et 291 sur 706 dans une partie de contrôle) : ils échangent à peu près deux fois moins souvent que prévu, ce qui les affaiblit sans doute. Ils ne jouent donc pas exactement comme dans leur source.

Sur le site, croiser sa propre offre retirerait toutes ses offres dans la couleur, d'après l'auteur de FiggieServer. Mon moteur refuse l'action. Je ne l'ai pas vérifié sur le site.

Tout reste mesuré contre des bots simulés. Ces gains ne sont pas des gains réels sur figgie.com.

## Reproduire

```bash
cd projets/bot-figgie
python3 -m unittest                                                  # les 124 tests, environ 15 s
python3 -m figgie.tournoi --site --candidates adaptatif_v4c --rounds 10 --deals 300 --no-tables \
    --opponents marginal --references exploiteur imitateur --out tournoi_v4c.json
python3 -m figgie.tournoi --site --candidates adaptatif_v4b --rounds 10 --deals 300 --no-tables \
    --opponents marginal --references imitateur --out tournoi_v4b.json
python3 -m figgie.tournoi --site --candidates adaptatif_v4c adaptatif_v4b marginal --rounds 10 --deals 300 --no-tables \
    --opponents inactif --references fondamentaliste fondamentaliste_35 vendeur mante parieur \
    --out tournoi_references.json
```

Le tournoi affiche maintenant son avancement pendant qu'il tourne. Pour revenir exactement au code de cette phase : `git checkout phase5g-figgie`.
