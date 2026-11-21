# Phase 5b : jouer contre ses propres copies

*English version: [phase5b.en.md](phase5b.en.md)*

La phase 5 s'est arrêtée sur un défaut précis. Le bot adaptatif avait appris sur des tables où les autres joueurs ne s'adaptaient pas. Mis à plusieurs à la même table, ses copies reconnaissaient la même situation, resserraient leurs prix au même moment, et un sniper seul en profitait. Cette phase corrige ce défaut. Elle ajoute aussi trois idées trouvées en lisant ce que d'autres ont écrit sur Figgie.

Le bilan est contrasté. Le nouveau bot, la v3, bat la v2 et le marginal en tête-à-tête, avec plus d'écart qu'avant. Ses copies ne se font plus exploiter par le sniper, le marginal ni le preneur trouvé en phase 5. Mais il échoue encore au test de minorité, pour les mêmes raisons que le marginal : l'exploiteur de la phase 4 et, à 4 joueurs, le bayésien gagnent face à ses copies. Et la recherche automatique trouve un nouvel exploiteur, qui lui prend 6,25 $ par manche. Aucun bot n'est promu.

## Ce que j'ai lu avant de commencer

Avant d'écrire du code, j'ai lu ce qui existe sur Figgie : la vidéo de Jane Street où deux traders commentent trois manches, un fil de r/quant, les leçons de David Jiang sur theory-a.com, une discussion sur Hacker News, les articles de Rob Kohr, de Logan Seaburg et de Ross Rheingans-Yoo, l'article arXiv 2110.00879, plusieurs dépôts GitHub de bots, et l'article de Rasmus Suonio sur LinkedIn, avec son code et ses journaux de parties.

Plusieurs choses que le simulateur supposait sont confirmées. Dans la vidéo, deux joueurs finissent à égalité et se partagent le reste du pot : c'est exactement le calcul du simulateur. Sur Hacker News, un joueur raconte que les ordres disparaissent après chaque échange, autre règle supposée depuis la phase 1. Les traders de la vidéo font aussi le même calcul que le marginal : la carte qui décide de la majorité vaut beaucoup plus que 10 $.

Trois idées n'étaient pas encore dans nos bots, et elles sont devenues les trois premières étapes de cette phase.

1. **Compter les cartes avec les ventes proposées.** L'idée vient de KnifeEdge, sur r/quant. Selon lui, le site refuse une offre de vente quand on n'a pas la carte, et notre simulateur fait pareil. Celui qui propose de vendre un trèfle en a donc au moins un, même s'il annule son offre ensuite. Notre comptage n'utilisait que les échanges.
2. **Jouer avec le temps.** C'est l'idée qui revient le plus : dans la vidéo, chez David Jiang, dans un des dépôts. Les traders de la vidéo prennent leur temps au début et deviennent agressifs dans les 40 dernières secondes. Nos bots cotaient avec le même écart de la première à la dernière seconde.
3. **Jouer selon sa main.** La vidéo et le fil Reddit le disent tous les deux : une main concentrée sur une couleur se joue fort, une main plate se joue discrètement.

## Étape 1 : un résultat nul

Le nouveau comptage est simple. Une offre de vente prouve qu'on a au moins une carte de cette couleur. Un achat en ajoute une. Une vente en retire une, si on en connaissait une. Le test reprend l'exemple de KnifeEdge à 5 joueurs : avec 5 trèfles en main et ce qu'on voit passer sur le marché, on sait qu'il y a au moins 9 trèfles en jeu, donc 10 ou 12.

J'ai mis ce comptage dans une copie du marginal, le « compteur », et je l'ai opposé au marginal sur 400 donnes dupliquées (graine 2).

| | 4 joueurs | 5 joueurs |
|---|---|---|
| compteur seul face au marginal corrigé | -0,78 [-1,91 ; +0,36] | -0,81 [-1,75 ; +0,14] |
| compteur seul face au marginal | +0,12 [-1,08 ; +1,32] | -1,48 [-2,67 ; -0,29] |
| marginal seul face au compteur | -0,15 [-1,28 ; +0,97] | +2,05 [+0,86 ; +3,25] |

En dollars par manche, avec l'intervalle de confiance à 95 %.

Le compteur ne fait pas mieux, et à 5 joueurs il fait même un peu moins bien. La raison est arithmétique. Avec 10 cartes en main, presque tout le monde a au moins une carte de chaque couleur. Savoir qu'un joueur en a « au moins une » n'apprend presque rien. Le taux de bonne couleur objectif devinée le confirme : 40,0 % sans le nouveau comptage, 40,1 % avec, sur une table de marginaux. Il ne change pas non plus entre 30 et 200 secondes, parce que le marché est déjà mort à ce moment-là. J'ai gardé le code et le test, mais le marginal reste la base.

## Étape 2 : un écart qui se resserre avec le temps

Le spread et la marge du bot peuvent maintenant changer pendant la manche. Ils partent d'une valeur de début et vont, en ligne droite, vers une valeur de fin à la dernière seconde. Le test le vérifie sur un bot qui passe d'un spread de 8 $ à 2 $ : en début de manche, il ne propose pas plus de 4 $ à l'achat ; à partir de 200 secondes, il monte à 9 $.

J'ai réglé ces deux nouveaux nombres comme en phase 2, sur 150 donnes de réglage (graine 2), à 4 joueurs, avec le test de minorité. Le critère est la pire borne basse sur tous les adversaires. Ce critère garde le réglage constant (8 $, 1 $), avec une pire borne de -8,0. Mais le tableau montre un compromis :

| Réglage (début → fin) | contre le sniper | contre le lecteur | exploiteur seul |
|---|---|---|---|
| spread 8 → 8, marge 1 → 1 | +13,5 | +0,3 | +5,9 |
| spread 8 → 3, marge 1 → 1 | +20,8 | +3,1 | +6,8 |

En dollars par manche. La dernière colonne est le gain de l'exploiteur seul face aux copies du bot.

Resserrer en fin de manche rapporte nettement plus contre le sniper et le lecteur, mais laisse un peu plus à l'exploiteur. Une marge de fin à 0 $ est moins bonne partout. Aucun réglage fixe ne gagne sur toutes les colonnes. C'est justement le genre de choix que le bot adaptatif peut faire table par table. J'ai donc ajouté deux réglages qui se resserrent, (8 → 3, 1 → 1) et (12 → 4, 3 → 1), aux quatre réglages de la phase 5.

## Étape 3 : s'entraîner contre ses copies

C'est la correction du défaut de la phase 5. Le principe vient de la théorie des jeux, sous le nom de *fictitious play* : on entraîne le bot contre des tables où jouent ses versions précédentes, puis on recommence avec la nouvelle version, jusqu'à ce que ses choix ne changent plus.

Concrètement, chaque tour tire 80 tables à 4 ou 5 joueurs. Environ une sur deux ressemble au test de minorité : toute la table est faite de copies d'une version précédente du bot adaptatif, sauf un joueur pris dans la ligue. Les autres tables sont tirées dans la ligue, versions précédentes comprises. Sur chaque table, je mesure les six réglages sur 40 donnes dupliquées, en parties de 3 manches. La première manche ne compte pas : les versions adaptatives n'y ont pas encore choisi leur réglage.

Le bot reçoit aussi une nouvelle donnée : la force de sa main. Je calcule la probabilité de chaque couleur objectif d'après ma seule donne. Si la plus forte dépasse 40 %, la main est « forte », ce qui arrive dans environ 23 % des donnes. Les gains sont mesurés séparément pour les mains fortes et les mains plates.

J'ai fait deux tours. Le premier avait la v2 aux tables (graine 12), le second la v2 et la v3 du premier tour (graine 13). Chaque table est jugée par un modèle construit sur les 79 autres :

| | Tour 1 | Tour 2 |
|---|---|---|
| réglage fixe (8, 1) | +9,28 | +7,74 |
| réglage choisi | +11,68 | +10,00 |
| écart au fixe | +2,40 [+1,91 ; +2,89] | +2,26 [+1,71 ; +2,80] |
| meilleur réglage, connu après coup | +12,60 | +11,25 |

En dollars par manche. Le choix récupère 64 à 72 % de ce qu'on pourrait gagner en connaissant la réponse, contre moins de la moitié pour la v2.

Pour savoir si les choix se stabilisent, j'ai regardé ce que choisit le modèle sur les tables façon test de minorité, en le construisant sans la table jugée :

| Tables façon minorité | Tour 1 | Tour 2 |
|---|---|---|
| main plate | 8 → 3 sur 36 tables, 12 → 4 sur 7 | 8 → 3 sur 37 tables, 12 → 4 sur 3, autres sur 2 |
| main forte | 8 → 3 sur 22, 12 → 4 sur 21 | 8 → 3 sur 24, 12 → 4 sur 18 |

Les choix bougent peu d'un tour à l'autre, et l'écart au fixe non plus. Je me suis arrêté à deux tours. Avec une main plate, le bot garde son spread de 8 $ et le resserre à 3 $ en fin de manche. Avec une main forte, il hésite entre ce réglage et un spread de 12 $ qui se resserre à 4 $. Le modèle du tour 2 est devenu celui de la v3.

## Le tournoi

Comme en phase 5 : parties de 10 manches, 300 donnes dupliquées (graine 1), et les deux exploiteurs de la phase 4 dans le test de minorité. Le preneur de la phase 5 est mesuré à part, sur les mêmes donnes.

| | marginal | adaptatif v2 | adaptatif v3 |
|---|---|---|---|
| contre le marginal, 4 j. | | +2,00 [+1,64 ; +2,37] | +8,48 [+8,10 ; +8,87] |
| contre le marginal, 5 j. | | +3,47 [+3,15 ; +3,79] | +4,78 [+4,49 ; +5,07] |
| contre le sniper, 4 j. | +15,60 | +16,70 | +26,23 |
| contre le lecteur, 4 j. | +0,97 | +2,21 | +5,20 |
| contre le lecteur, 5 j. | +5,52 | +8,33 | +10,97 |
| contre l'exploiteur, 4 j. | +19,84 | +17,14 | +20,27 |
| sniper seul, 4 j. | -0,94 [-1,39 ; -0,48] | +3,72 [+3,24 ; +4,21] | -4,86 [-5,35 ; -4,37] |
| sniper seul, 5 j. | -1,28 [-1,64 ; -0,91] | +2,80 [+2,42 ; +3,19] | -0,27 [-0,64 ; +0,09] |
| marginal seul, 4 j. | | +1,29 [+0,95 ; +1,64] | -3,29 [-3,61 ; -2,98] |
| marginal seul, 5 j. | | -0,26 [-0,56 ; +0,04] | -2,34 [-2,61 ; -2,07] |
| preneur seul, 4 j. | -0,70 [-1,11 ; -0,29] | +5,62 [+5,16 ; +6,08] | -9,87 [-10,28 ; -9,47] |
| preneur seul, 5 j. | -1,30 [-1,69 ; -0,92] | +4,36 [+3,91 ; +4,80] | -4,17 [-4,59 ; -3,76] |
| bayésien seul, 4 j. | +1,14 [+0,56 ; +1,72] | +0,10 [-0,47 ; +0,67] | +1,43 [+0,84 ; +2,02] |
| bayésien seul, 5 j. | -0,61 [-1,00 ; -0,22] | -1,69 [-2,06 ; -1,33] | +0,27 [-0,12 ; +0,67] |
| exploiteur seul, 4 j. | +4,32 [+3,85 ; +4,80] | +1,54 [+1,06 ; +2,02] | +5,27 [+4,83 ; +5,71] |
| exploiteur seul, 5 j. | +7,24 [+6,85 ; +7,64] | +3,02 [+2,64 ; +3,39] | +7,79 [+7,46 ; +8,12] |

En dollars par manche. Les lignes « seul » donnent le gain de l'adversaire seul face aux copies du candidat : plus il est haut, plus le candidat se fait exploiter.

Contre le reste du zoo, la v3 gagne nettement contre chaque adversaire, comme les deux autres. Aux tables anormales (100 donnes, 10 manches), elle fait comme la v2 : +19,3 $ avec le joueur inactif, +119,3 $ avec le spammeur et +20,3 $ avec les menteurs.

**Le verdict de la règle d'entrée.** La v3 bat nettement tout le zoo, à 4 et à 5 joueurs. Elle échoue au test de minorité à 4 joueurs, à cause de l'exploiteur seul et du bayésien seul, et à 5 joueurs à cause de l'exploiteur seul. Le marginal échoue exactement aux mêmes endroits. Aucun bot n'est promu, et le marginal reste la référence.

**Le bot s'améliore-t-il ?** En tête-à-tête, oui, nettement : il gagne plus que la v2 contre tous les adversaires, et quatre fois plus contre le marginal à 4 joueurs. Face aux exploiteurs, non, comme le montre la section suivante. Le défaut de la phase 5 est corrigé : le sniper, le marginal et le preneur perdaient de l'argent face aux copies du marginal, gagnaient face aux copies de la v2, et en perdent de nouveau face à celles de la v3, souvent plus que face au marginal. En revanche, la v3 rend à l'exploiteur de la phase 4 ce que la v2 lui avait pris. Face à lui, elle se retrouve au niveau du marginal, un peu en dessous.

## Pourquoi l'exploiteur gagne encore

J'ai regardé les réglages que choisissent trois copies de la v3 face à un adversaire seul, sur 20 parties de 10 manches. Face au sniper, elles prennent presque toujours le spread de 12 $ qui se resserre à 4 $, et le sniper perd alors 4,86 $ par manche. Face à l'exploiteur, au marginal et au bayésien, elles jouent presque toujours 8 $ qui se resserre à 3 $.

Contre l'exploiteur, ce choix est mauvais pour l'ensemble des copies. Le tableau de l'étape 2 le montrait déjà : l'exploiteur seul gagne 6,8 $ contre ce réglage, et 5,9 $ contre le réglage constant. Aucun des réglages que j'ai mesurés ne le fait passer sous zéro. Et comme Figgie est un jeu à somme nulle, ses +5,27 $ par manche coûtent en moyenne 1,76 $ à chacune des trois copies.

Chaque copie fait pourtant ce qu'on lui a appris : elle choisit le réglage qui lui rapporte le plus, sachant ce que font les autres. L'entraînement contre soi trouve justement ce genre de point stable, où personne n'a intérêt à changer seul. Le test de minorité demande autre chose : que les copies, ensemble, ne laissent rien au joueur seul. C'est une question d'équipe, et rien dans l'entraînement ne la pose.

## Exploiteurs

J'ai relancé la recherche d'exploiteurs de la phase 5 contre la v3, dans les mêmes conditions : 4 joueurs, parties de 10 manches, 60 réglages, puis 20, 100 et 300 donnes aux trois étapes (graines 5, 6 et 1).

Le gagnant n'est plus un preneur. C'est un « coteur serré » : il calcule ses valeurs comme le bayésien, cote avec un spread de 3 $ seulement, prend toute cotation qui lui laisse 3 $ de marge, et réagit en 0,2 seconde. Seul face à trois copies de la v3, il gagne +6,25 $ par manche [+5,71 ; +6,79]. Je l'ai mesuré contre les autres candidats, sur les mêmes 300 donnes :

| Seul face à des copies de | preneur (phase 5), 4 j. | preneur, 5 j. | coteur serré (phase 5b), 4 j. | coteur serré, 5 j. |
|---|---|---|---|---|
| marginal | -0,70 [-1,11 ; -0,29] | -1,30 [-1,69 ; -0,92] | +4,95 [+4,43 ; +5,48] | +4,80 [+4,45 ; +5,15] |
| adaptatif v2 | +5,62 [+5,16 ; +6,08] | +4,36 [+3,91 ; +4,80] | +1,49 [+1,01 ; +1,98] | +2,26 [+1,88 ; +2,64] |
| adaptatif v3 | -9,87 [-10,28 ; -9,47] | -4,17 [-4,59 ; -3,76] | +6,25 [+5,71 ; +6,79] | +5,85 [+5,51 ; +6,20] |

Gain de l'exploiteur, en dollars par manche.

Ce tableau ressemble à pierre-feuille-ciseaux. Le preneur bat la v2, qui résiste au coteur serré. Le coteur serré bat le marginal et la v3, qui résistent au preneur. Chaque candidat a un exploiteur qui lui prend entre 4 et 8 $ par manche, si l'on compte aussi l'exploiteur de la phase 4. La v3 a corrigé la faiblesse de la v2 et retrouvé celle du marginal. Dans le pire cas, elle est même la plus exploitable des trois : 6,25 $ par manche à 4 joueurs et 7,79 $ à 5 (l'exploiteur de la phase 4), contre 4,95 $ et 7,24 $ pour le marginal, 5,62 $ et 4,36 $ pour la v2.

## Ce que j'en retiens

Ce que les autres ont écrit sur Figgie m'a donné trois idées, et la plus évidente des trois n'a rien donné. Compter les ventes proposées paraissait malin. Le calcul montrait pourtant d'avance qu'avec des mains de 10 cartes, savoir qu'un joueur en a « au moins une » n'apprend presque rien.

Le défaut précis de la phase 5 s'est corrigé. Une fois entraîné contre ses propres copies, le bot ne se jette plus dans la guerre des prix qui faisait gagner le sniper et le preneur. Deux tours ont suffi pour que ses choix se stabilisent.

Les deux faiblesses du tournoi, l'exploiteur et le bayésien seuls, ne sont pas nouvelles. Le marginal les avait déjà, et face à ces adversaires la v3 joue presque comme lui. Pour les corriger, il faudrait soit un réglage qui prive l'exploiteur de ses gains, et aucun de ceux que j'ai mesurés ne le fait, soit un entraînement qui juge les copies ensemble.

La recherche d'exploiteurs montre la limite de la méthode. Chaque version corrige la faiblesse que la précédente laissait voir, et en rouvre une autre. Le marginal, la v2 et la v3 ont chacun un exploiteur qui leur prend 4 à 8 $ par manche. Tant que le bot choisit parmi quelques réglages fixes, un adversaire qui connaît ces réglages trouve toujours celui qu'il faut contrer. Pour en sortir, il faudrait un bot qui mélange ses réglages au hasard, ou dont le calcul de valeur laisse moins de prise.

## Limites

Tous les adversaires sont toujours des bots. Les gains mesurés ici, contre des bots simulés, ne disent rien du niveau face à des humains ni face aux bots du site.

Les journaux de Rasmus Suonio, enregistrés sur figgie.com, montrent d'ailleurs à quel point le simulateur s'éloigne du vrai marché. Sur ses 60 manches, il y a en moyenne 53 échanges par manche, et presque la moitié tombe dans la dernière minute. Sur nos tables simulées, il y en a entre 6 et 22, tous dans la première minute. Le site impose aussi qu'une nouvelle offre batte la meilleure offre en cours, alors que notre simulateur garde une cotation par joueur. Un bot réglé sur nos tables est donc réglé sur un marché qui ne ressemble pas à celui du site.

Le bot choisit entre six réglages seulement, et la force de la main tient en un seul seuil. Les deux tours d'entraînement portent sur 40 donnes par table, en parties de 3 manches. Le tournoi porte sur 300 donnes, avec des intervalles de l'ordre du dollar.

Les limites des phases précédentes tiennent toujours : temps de réaction inventés, argent qui repart de 350 $ à chaque manche.

## Reproduire

```bash
cd projets/bot-figgie
python3 -m unittest                                                  # les 103 tests, environ 10 s
python3 -m figgie.tune --players 4 --deals 150 --minority --spreads 8 10 12 --edges 1 \
    --spreads-late 3 5 8 --edges-late 1 0 --out reglage_temps_4j.json
python3 -m figgie.adapt --v3 1 --previous adaptatif_v2 --tables 80 --deals 40 --rounds 3 \
    --arms 6,3,6,3 8,1,8,1 10,3,10,3 12,3,12,3 8,1,3,1 12,3,4,1 --report entrainement_v3_1.json
python3 -m figgie.adapt --v3 2 --previous adaptatif_v2 adaptatif_v3_1 --tables 80 --deals 40 --rounds 3 \
    --arms 6,3,6,3 8,1,8,1 10,3,10,3 12,3,12,3 8,1,3,1 12,3,4,1 --report entrainement_v3_2.json
cp modeles/adaptation_v3_2.json modeles/adaptation_v3.json
python3 -m figgie.tournoi --candidates adaptatif_v3 --rounds 10 --deals 300 --table-deals 100 \
    --references heuristique sniper bayesien marginal exploiteur exploiteur_lecteur --out tournoi_v3.json
python3 -m figgie.exploit --target adaptatif_v3 --players 4 --rounds 10 --deals 20 100 300
```

Chaque tour d'entraînement prend environ 50 minutes sur 10 cœurs, le tournoi deux heures et demie. Pour revenir exactement au code de cette phase : `git checkout phase5b-figgie`.

## Et ensuite

La phase 6, le site réel, attend toujours un accord écrit de Jane Street. Avant de la demander, je veux des résultats qui aient un sens face au vrai marché. La suite la plus utile est donc de rapprocher le simulateur du site : un adversaire simulé réglé sur les journaux de Rasmus Suonio, la règle d'une seule offre par côté, et le rejeu de vraies manches. Viendront ensuite un calcul exact de la valeur des cartes à la place du Monte Carlo, de nouveaux adversaires, et un entraînement qui juge les copies ensemble.
