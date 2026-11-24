# Phase 5i : ce que mesure le test de minorité

*English version: [phase5i.en.md](phase5i.en.md)*

Depuis la phase 4, aucun de mes bots ne passe le test de minorité : on met une référence seule face à trois copies du candidat, et si elle gagne nettement de l'argent, le candidat est refusé. Les phases 5f, 5g et 5h ont essayé de changer la façon dont les copies choisissent leur réglage, sans faire tomber l'exploiteur. La phase 5h proposait de changer de levier. Avant de toucher au bot, j'ai voulu savoir d'où vient exactement l'argent que l'exploiteur prend aux copies.

Le diagnostic montre que les copies ne paient pas trop cher les cartes de l'exploiteur. Chaque achat rapporte à la copie qui le fait. Ce qu'elles perdent, c'est la majorité qu'elles se prennent entre elles. J'ai donc remplacé le test de minorité par une table mixte : la référence, le candidat et des Hard simulés, à la même table. Avec ce nouveau test, la v4c est refusée encore plus nettement : à une table proche du site, l'exploiteur fait environ 10 $ de mieux qu'elle par manche. Aucun bot n'est promu.

## D'où vient le gain de l'exploiteur

J'ai rejoué 40 parties de 10 manches, l'exploiteur seul face à trois copies de la v4c, à 4 joueurs, et rangé chacun de ses échanges : achat ou vente, couleur objectif ou non. Chaque carte est comptée à sa valeur de fin de manche, 10 $ si elle est de la couleur objectif, 0 sinon. Ce qui reste du gain, une fois retirés les échanges et les cartes de départ, c'est la majorité. Par manche :

| Exploiteur seul face à 3 v4c | $ par manche | échanges par manche |
|---|---|---|
| ventes de cartes hors objectif | +23,90 | 2,46 |
| ventes de cartes objectif | +0,49 | 1,12 |
| achats | -0,11 | 0,06 |
| cartes de départ moins la mise | -26,90 | |
| majorité | +3,88 | |
| total | +1,26 | |

Ce sont des parties simples, sans donnes dupliquées : le total est bruité, mais la répartition est nette. L'exploiteur n'achète presque jamais. Il vend aux copies, autour de 10 $, des cartes qui, sept fois sur dix, ne valent rien à la fin.

## Pourquoi les copies achètent

J'ai ensuite remplacé les copies par une sonde, la v4c qui note chacune de ses décisions d'achat : la valeur qu'elle donnait à la carte et la probabilité qu'elle lisait sur le marché que la couleur soit l'objectif. Pour chaque carte achetée, j'ai aussi calculé ce qu'elle a vraiment rapporté, majorité comprise, en la rendant au vendeur à la fin de la manche et en recalculant les gains. Moyenne par carte vendue par l'exploiteur :

| | $ par carte |
|---|---|
| prix payé | 9,93 |
| valeur que la copie lui donnait | 16,12 |
| ce que la carte rapporte à la copie qui l'achète | 17,32 |
| ce que la carte rapporte aux trois copies ensemble | 4,50 |

Deux choses ressortent. Les copies lisent bien la couleur objectif : elles lui donnent environ 25 % de chances, et 29 % des cartes achetées dans cette tranche étaient objectif. Elles ne surestiment donc pas la couleur. Et chaque achat rapporte bien à la copie qui le fait, environ 7 $ de plus que le prix. Mais l'essentiel de ce gain, c'est de la majorité prise à une autre copie. Pour le groupe, une carte payée 9,93 $ n'en rapporte que 4,50. La v3 donne la même image : 9,55 $ payés, 17,76 $ pour l'acheteuse, 4,29 $ pour les copies.

Ce calcul ne tient pas compte des échanges que la carte aurait changés plus tard dans la manche. Il donne un ordre de grandeur, pas une mesure exacte.

Le test de minorité punit donc un comportement qui rapporte quand le bot joue seul. Trois copies qui se disputent la même majorité perdent ensemble, même si chacune joue bien pour elle-même. Rendre les copies plus prudentes à l'achat les ferait sans doute passer le test, mais coûterait au bot quand il est seul.

## Le nouveau test : la table mixte

À 4 joueurs, la table mixte réunit la référence, le candidat et deux Hard simulés, qui imitent les bots du site. À 5 joueurs, trois Hard. Pour chaque donne, je joue toutes les rotations de [référence, candidat, Hard, Hard], puis celles de [candidat, référence, Hard, Hard] : chacun passe par chaque siège, devant et derrière l'autre. Dans chaque partie, je lis le gain de la référence et celui du candidat, et je garde l'écart. Le candidat est refusé si l'écart d'une référence a un intervalle de confiance entièrement au-dessus de 0. Le reste de la règle d'entrée ne change pas. Le test de minorité reste calculable, et je donne son verdict à côté.

Je change la règle après qu'un bot y a échoué, et c'est le genre de chose qui permet de se donner raison à bon compte. C'est pour ça que je l'écris ici, avec le diagnostic qui la justifie et l'ancien verdict en regard. Le nouveau test se révèle d'ailleurs plus sévère pour la v4c que l'ancien.

Les tests passent par deux seams. Le premier vérifie que la règle d'entrée refuse un candidat dès qu'un écart de la table mixte est nettement positif, sur des intervalles écrits à la main. Le second porte sur le calcul de l'écart : avec une référence et un candidat identiques, chaque partie a sa jumelle où les deux bots ont échangé leurs sièges, donc l'écart doit valoir exactement 0 sur chaque donne. Ce test a attrapé un vrai bug dans ma première version : quand les deux bots étaient de la même classe, l'échange de sièges n'était pas détecté. Un dernier test vérifie le signe : un bayésien face à un bot aléatoire donne un écart positif, et le test échoue bien si j'inverse le signe exprès.

La relecture du code a aussi trouvé un défaut dans ma toute première version : je calculais le gain de la référence et celui du candidat dans deux séries de parties différentes, où ils n'occupaient pas les mêmes sièges. L'écart n'était donc pas apparié. J'ai arrêté le tournoi qui tournait, corrigé, et tout relancé.

## Calibration : est-ce que le test attrape encore le marginal ?

Le test de minorité est né en phase 4, quand l'exploiteur gagnait face aux copies du marginal. Avant le tournoi, j'ai vérifié que la table mixte voit toujours ce cas, sur 100 donnes de la graine 7. Écart référence moins candidat, en dollars par manche :

| | marginal, 4 j. | marginal, 5 j. | v4c, 4 j. | v4c, 5 j. |
|---|---|---|---|---|
| exploiteur | +22,36 [+21,00 ; +23,73] | +23,78 [+22,70 ; +24,87] | +10,06 [+8,62 ; +11,50] | +9,78 [+8,42 ; +11,14] |
| v3 | +4,15 [+3,07 ; +5,24] | +5,00 [+4,17 ; +5,83] | -7,56 [-8,95 ; -6,16] | -11,71 [-13,12 ; -10,29] |

Le test attrape bien le marginal. Mais il refuse aussi la v4c, et de 10 $, trois fois ce que montrait le test de minorité.

Pour savoir qui prend l'argent de qui, j'ai compté 30 parties à la table [exploiteur, v4c, Hard, Hard], dans une seule disposition des sièges, chaque échange compté à la valeur finale de la carte, sans la majorité. Par manche, l'exploiteur gagne net 38,97 $ sur les deux Hard et 10,84 $ sur la v4c. La v4c gagne 10,37 $ sur les Hard. Même seule de son espèce à la table, la v4c continue d'acheter les cartes hors objectif de l'exploiteur, même si une partie de cet argent lui revient sûrement par la majorité. Et surtout, l'exploiteur prend aux Hard presque quatre fois plus que la v4c.

## Le tournoi

Les mêmes 300 donnes qu'aux phases précédentes (graine 1), la règle du site, des parties de 10 manches. Contre le zoo, je retrouve exactement les chiffres de la v4c de la phase 5f : +7,75 $ et +4,59 $ contre le marginal, à 4 et 5 joueurs. Le moteur est bien déterministe, et la règle d'entrée sans test d'exploitation passe toujours.

À la table mixte, l'écart de gain référence moins candidat, en dollars par manche, à côté du gain de la référence seule face aux copies au test de minorité de la phase 5f :

| Référence | table mixte, 4 j. | table mixte, 5 j. | minorité 5f, 4 j. | minorité 5f, 5 j. |
|---|---|---|---|---|
| exploiteur | **+10,43** [+9,67 ; +11,20] | **+8,81** [+8,17 ; +9,46] | +3,15 | +4,65 |
| bayésien | **+3,65** [+2,79 ; +4,52] | **+7,13** [+6,44 ; +7,81] | -2,54 | -1,20 |
| v4b | -0,44 [-0,91 ; +0,04] | -0,38 [-0,70 ; -0,06] | +0,16 | +0,32 |
| vendeur | -7,46 [-8,21 ; -6,70] | -10,08 [-10,74 ; -9,41] | | |
| v3 | -7,91 [-8,69 ; -7,14] | -11,90 [-12,64 ; -11,15] | +0,94 | +2,46 |
| marginal | -12,58 [-13,33 ; -11,83] | -16,45 [-17,14 ; -15,76] | -0,80 | +0,77 |
| exploiteur lecteur | -13,91 [-14,71 ; -13,12] | -16,50 [-17,25 ; -15,75] | -5,05 | -1,96 |
| parieur | -21,10 [-22,11 ; -20,09] | -24,57 [-25,42 ; -23,73] | | |
| mante | -31,08 [-32,02 ; -30,14] | -35,20 [-35,98 ; -34,42] | | |
| sniper | -34,09 [-35,03 ; -33,15] | -31,88 [-32,59 ; -31,17] | -4,87 | -3,80 |
| fondamentaliste (r = 1,7) | -35,98 [-37,06 ; -34,90] | -32,49 [-33,30 ; -31,67] | | |
| fondamentaliste (r = 3,5) | -39,82 [-40,85 ; -38,79] | -37,79 [-38,45 ; -37,13] | | |
| imitateur | -44,72 [-45,85 ; -43,59] | -42,06 [-43,00 ; -41,11] | | |
| Hard simulé | -47,82 [-49,20 ; -46,45] | -43,22 [-44,19 ; -42,25] | -14,68 | -12,60 |
| heuristique | -69,35 [-70,59 ; -68,11] | -71,32 [-72,36 ; -70,27] | -26,75 | -26,96 |

Les deux colonnes ne mesurent pas la même chose. La table mixte compare deux gains à la même table, la minorité donne le gain de la référence seule face aux copies : les ordres de grandeur ne se comparent pas, seuls les signes se lisent ensemble. Les cases vides sont des références ajoutées après la phase 5f.

En gras, les références qui font nettement mieux que la v4c à la table mixte : la règle d'entrée échoue à 4 et à 5 joueurs, à cause de l'exploiteur et du bayésien. Avec l'ancienne règle, elle échouait aussi, à cause de l'exploiteur, de la v3 et du marginal à 5 joueurs. Le bot ne progresse donc pas : la v4c n'a pas changé, et la nouvelle règle la refuse comme l'ancienne. Aucun bot n'est promu, et la v4c reste mon meilleur bot. Tous ces chiffres sont mesurés contre des bots simulés : ce ne sont pas des gains réels.

## Ce que j'en retiens

Les deux tests ne voient pas les mêmes adversaires. La v3 et le marginal gagnaient face aux copies de la v4c, mais à une table mixte, ils font 8 à 16 $ de moins qu'elle par manche : ils profitaient surtout de la course à la majorité entre copies. À l'inverse, le bayésien perdait face aux copies, mais à une table avec des Hard, il fait 4 à 7 $ de mieux que la v4c.

L'exploiteur et le bayésien ont un point commun : tous deux sont des bots bayésiens, qui estiment la valeur d'une carte à partir de leur seule main, sans le Monte Carlo de la majorité. L'exploiteur cote simplement plus serré. À une table de Hard simulés, ce bot simple fait mieux que mon meilleur bot. Le test de minorité le cachait derrière la course à la majorité entre copies.

Un premier diagnostic, l'exploiteur puis la v4c seuls face à trois Hard simulés, sur 40 parties de 10 manches, montre d'où vient la différence. L'exploiteur gagne +46,68 $ par manche, presque tout en vendant aux Hard des cartes hors objectif : 6,6 cartes par manche autour de 9,94 $, pour +65,83 $. Il ne gagne la majorité que dans 2 % des manches. La v4c gagne +32,81 $. Elle gagne la majorité dans 40 % des manches (+36,33 $), mais elle achète 1,9 carte hors objectif par manche, surtout dans la première minute, et y perd 18 $. Elle vend aussi moins de cartes hors objectif, et moins cher : 4,6 cartes par manche à 8,72 $ en moyenne, quand les Hard prennent ses cotations.

## Et ensuite

La phase 5j partira de là : pourquoi la v4c n'arrive pas à vendre aux Hard comme le fait l'exploiteur, et si ses achats de la première minute valent ce qu'ils coûtent. Avant de changer le bot, je vérifierai sur les vraies manches de Rasmus si les vrais bots du site achètent vraiment les cartes hors objectif vers 10 $, comme mes Hard simulés. En phase 5e, le bayésien, qui vend ses cartes à 10 $, finissait dernier sur les vraies manches rejouées. Le Hard simulé est peut-être trop bon client. Un premier coup d'œil va dans ce sens : sur les 60 vraies manches, les bots du site paient au bot de Rasmus 4,19 $ en moyenne une carte hors objectif, et seulement 6 % de ces achats se font à 9 $ ou plus. Dans ma simulation, les Hard simulés paient ces cartes 9,81 $ à l'exploiteur, à 9 $ ou plus dans 83 % des cas. Ce n'est pas encore une preuve, puisque le bot de Rasmus demande peut-être simplement moins cher. Je proposerai un plan avant de commencer.

## Limites

Le diagnostic des achats compte chaque carte en la rendant au vendeur à la fin de la manche. Il ne voit pas les échanges que cette carte aurait changés ensuite. Le comptage de qui prend l'argent de qui à la table mixte porte sur une seule disposition des sièges et 30 parties, il est plus bruité que le tournoi.

Le nouveau test dépend du remplissant. Avec des Hard simulés, il mesure qui joue le mieux contre eux autant que ce que la référence prend au candidat. Si le Hard simulé est loin des vrais bots du site, le test l'est aussi.

À la table mixte, la référence et le candidat sont toujours voisins, l'un juste devant l'autre. À 5 joueurs, les places où ils sont séparés par un Hard ne sont jamais jouées. Le test de l'écart nul vérifie que l'échange de sièges est bien suivi, pas quels sièges sont lus : c'est le test de signe, et une vérification à la main, qui couvrent ce point.

Le tournoi ne garde que les moyennes de chaque case. Pour la table mixte, ce n'est pas un problème, puisque l'écart est apparié donne par donne avant d'en faire la moyenne.

Tout reste mesuré contre des bots simulés. Ces gains ne sont pas des gains réels sur figgie.com.

## Reproduire

```bash
cd projets/bot-figgie
python3 -m unittest                                                  # les 131 tests, environ 5 s
python3 -m figgie.tournoi --site --candidates adaptatif_v4c --rounds 10 --deals 300 --no-tables \
    --opponents heuristique sniper bayesien marginal --references \
    --mixed hard_simule heuristique sniper bayesien marginal adaptatif_v3 adaptatif_v4b exploiteur \
        exploiteur_lecteur imitateur fondamentaliste fondamentaliste_35 vendeur mante parieur \
    --out tournoi_mixte.json
python3 -m figgie.tournoi --site --seed 7 --candidates marginal adaptatif_v4c --rounds 10 --deals 100 --no-tables \
    --opponents --references --mixed exploiteur adaptatif_v3 --out calibration.json
```

Le tournoi prend environ 6 h 20 sur 10 cœurs, la calibration 20 min. `--references` sans nom évite de recalculer le test de minorité. Depuis la phase 5j, la table mixte prend par défaut le Hard recalé : sur le code d'après, ajoutez `--filler hard_simule` pour retrouver ces chiffres. Pour revenir exactement au code de cette phase : `git checkout phase5i-figgie`.
