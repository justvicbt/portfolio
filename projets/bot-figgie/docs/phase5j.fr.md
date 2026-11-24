# Phase 5j : un Hard simulé qui ne paie plus trop cher

*English version: [phase5j.en.md](phase5j.en.md)*

La phase 5i s'est terminée sur une surprise : à une table de Hard simulés, l'exploiteur, un simple bot bayésien qui cote serré, faisait environ 10 $ de mieux par manche que la v4c. Il vendait aux Hard des cartes hors objectif vers 10 $. Un premier coup d'œil aux vraies manches de Rasmus laissait penser que les vrais bots du site ne paient pas ces cartes aussi cher. Cette phase vérifie ce point, puis recalibre le Hard simulé et rejoue la règle d'entrée avec lui.

Le Hard simulé était bien trop bon client. Recalé, il ne prend presque plus les offres de vente chères hors objectif, comme les vrais bots du site. Face à lui, l'exploiteur et le bayésien perdent de l'argent, et la v4c qui se tait pendant la première minute devient le meilleur de mes bots.

Au tournoi, aucun des deux candidats ne passe la règle d'entrée, et aucun bot n'est promu. La v4c est refusée par le Hard recalé lui-même : à la table mixte, il fait 9,86 $ de mieux qu'elle par manche à 4 joueurs. La v4c qui se tait 60 s fait mieux que toutes les références à la table mixte à 4 joueurs, mais elle ne bat plus le marginal face à trois de ses copies (-0,06 $ par manche à 4 joueurs, -3,44 $ à 5), et l'exploiteur lecteur fait 4,57 $ de mieux qu'elle à 5 joueurs.

## Les vrais bots du site prennent-ils les offres à 10 $ ?

Pour chaque offre de vente devenue la meilleure de sa couleur, j'ai regardé comment elle finit : prise par quelqu'un, remplacée par une offre moins chère, retirée, effacée par un échange (après chaque échange, le site vide tout le carnet, dans les quatre couleurs), ou encore là à la fin de la manche. J'ai fait la même mesure sur les 60 vraies manches de Rasmus et sur des manches simulées, un bot seul face à trois Hard simulés. Part des offres de vente prises par un bot Hard, dans les couleurs hors objectif :

| Prix de l'offre | vraies manches (offres du bot de Rasmus) | simulation (offres de l'exploiteur) | simulation (offres de la v4c) |
|---|---|---|---|
| 7 à 8 $ | 1 % sur 1119 | 36 % sur 228 | 30 % sur 880 |
| 9 à 10 $ | 1 % sur 594 | 18 % sur 2106 | 17 % sur 547 |
| 11 à 13 $ | 0 % sur 787 | 9 % sur 2157 | 11 % sur 455 |

Sur le site, une offre de vente à 7 $ ou plus dans une couleur hors objectif n'est presque jamais prise : elle est remplacée par une offre moins chère (60 à 70 % des cas) ou effacée par un échange (29 à 38 %). Mes Hard simulés en prenaient 9 à 36 % selon le prix, et c'est de là que venait l'essentiel du gain de l'exploiteur.

Le journal du site distingue le retrait d'une offre d'achat de celui d'une offre de vente. Mon moteur, lui, retire les deux côtés d'un coup. Sur les vraies manches, je ne compte donc que les retraits d'offre de vente. Les retraits sont rares : 0 à 5 % des offres.

## Le Hard recalé

En phase 5c, j'avais réglé le Hard simulé sur les échanges entre bots Hard : leur nombre, leur répartition dans la manche, leurs prix et la fréquence des cotations. Je n'avais jamais regardé comment ils réagissent à une offre de vente chère. J'ai ajouté à ces mesures la part des offres de vente d'un Hard qu'un autre Hard prend, en six tranches de prix et de couleur, et relancé la même recherche au hasard : 3000 réglages sur 30 manches, les 10 meilleurs revérifiés sur 90 autres.

Le réglage retenu n'a pas besoin de paramètre nouveau. Il donne moins de valeur à la couleur objectif (16 $ au lieu de 30 $ pour une probabilité de 1), il est presque d'accord avec les autres Hard sur la valeur des cartes (un écart tiré au hasard d'écart-type 1 $ au lieu de 6 $), et sa marge est plus petite (3 $ au lieu de 6 $) et fond plus vite au fil de la manche. Part des offres de vente d'un Hard qu'un autre Hard prend :

| | vraies manches | Hard recalé | Hard de la phase 5c |
|---|---|---|---|
| hors objectif, 1 à 3 $ | 30 % | 25 % | 7 % |
| hors objectif, 7 à 8 $ | 1,5 % | 2,0 % | 10,4 % |
| hors objectif, 9 à 13 $ | 1,0 % | 0,5 % | 4,8 % |
| objectif, 7 à 10 $ | 11,8 % | 12,2 % | 13,3 % |

Il y a un prix. Le Hard recalé échange moins avec les autres Hard que les vrais bots du site (5,3 échanges par paire et par manche, contre 9,4 ; celui de la phase 5c en faisait 6,5) et cote plus souvent (59 cotations par minute, contre 38). Sur les mesures de la phase 5c, son écart au site passe de 15,7 à 22,4. Il ne passerait plus le test de ressemblance de la phase 5c, qui demande que chaque mesure reste entre 0,6 et 1,5 fois celle du site : ses échanges entre Hard sont à 0,56 fois. Je garde donc l'ancien Hard tel quel, comme adversaire, et j'ajoute le nouveau sous le nom `hard_simule_v2`.

Face à l'exploiteur, il se comporte maintenant comme les vrais bots face à Rasmus : les offres hors objectif de l'exploiteur à 9 ou 10 $ ne sont plus prises qu'une fois sur cent.

Le seam de cette mesure est la fonction qui dit comment finit chaque offre de vente. Je l'ai testée sur un fil écrit à la main, avec une offre prise, une remplacée, une retirée, une effacée et une encore là à la fin. Pour vérifier que le test peut échouer, je l'ai faussé exprès en acceptant comme « prise » n'importe quel échange de la couleur, et il a échoué.

La relecture du code a trouvé deux erreurs dans ma première version de cette fonction. Elle ne fermait que l'offre de la couleur échangée, alors qu'un échange vide tout le carnet : une offre d'une autre couleur restait « affichée » dans ma mesure, et un échange plus tard à son prix pouvait passer pour une prise. Et elle comptait le retrait d'une offre d'achat comme celui de l'offre de vente. J'ai ajouté au test un fil qui couvre ces deux cas, vu le test échouer, puis corrigé. Les parts prises n'ont presque pas bougé (30,4 % devient 30,0 % pour les offres à 1 à 3 $, le reste à 0,1 point près). La part des offres « remplacées » a baissé, au profit des « effacées ». J'ai relancé la recalibration avec la mesure corrigée : elle retient le même réglage, avec les mêmes dix meilleurs dans le même ordre. Le Hard recalé, et donc le tournoi, ne changent pas.

## Face au Hard recalé

Chaque bot seul face à trois Hard recalés, sur 40 parties de 10 manches à 4 joueurs, toujours au même siège (ces parties simples sont plus bruitées qu'un tournoi en donnes dupliquées). Gain par manche :

| Bot | face au Hard recalé | face au Hard de la phase 5c |
|---|---|---|
| v4c qui se tait 60 s | **+12,56** | |
| v4c qui se tait 30 s | +3,49 | |
| v3 | -3,61 | |
| marginal | -6,16 | |
| v4c | -9,18 | +32,81 |
| exploiteur | -12,33 | +46,68 |
| bayésien | -28,73 | |

Les cases vides n'ont pas été mesurées dans ces parties simples. Le classement s'inverse. L'exploiteur, qui vivait de ses ventes aux Hard, perd maintenant 12 $ par manche. La v4c perd aussi, et sa décomposition montre pourquoi : elle achète 2,6 cartes hors objectif par manche dans la première minute, autour de 10 $, et y perd 20 $ par manche. La majorité lui rapporte 41 $, mais pas assez pour compenser.

La v4c qui n'envoie aucun ordre pendant la première minute existe depuis la phase 5g, inspirée de l'article de DiSilvio, Luo et Ozerov (arXiv 2110.00879), qui trouvaient qu'échanger tôt coûte. En phase 5g, face à l'ancien Hard, elle perdait environ 8 $ par manche contre le marginal, et je l'avais écartée. Face au Hard recalé, elle fait 22 $ de mieux que la v4c par manche.

Ce classement rejoint celui du rejeu des vraies manches sur le papier, en phase 5e : tous mes bots y perdaient, la v4 était la meilleure et le bayésien le dernier.

## La table mixte avec le Hard recalé

La table mixte de la règle d'entrée prend maintenant le Hard recalé comme remplissant. J'ai d'abord vérifié ce qu'elle donne sur 50 donnes de la graine 7. Écart référence moins candidat, en dollars par manche :

| | marginal, 4 j. | marginal, 5 j. | v4c, 4 j. | v4c, 5 j. | v4c calme 60 s, 4 j. | v4c calme 60 s, 5 j. |
|---|---|---|---|---|---|---|
| exploiteur | +1,34 [-1,35 ; +4,02] | +1,27 [-0,37 ; +2,91] | -6,65 [-9,60 ; -3,70] | -5,02 [-7,76 ; -2,29] | -13,97 [-16,36 ; -11,58] | -13,95 [-16,16 ; -11,75] |
| bayésien | +1,46 [-1,50 ; +4,43] | -4,97 [-7,66 ; -2,29] | -1,92 [-5,26 ; +1,42] | -4,18 [-7,43 ; -0,92] | -16,57 [-19,61 ; -13,54] | -19,59 [-22,45 ; -16,72] |

Avec ce remplissant, l'exploiteur ne fait plus nettement mieux que le marginal. L'exploitation que le test de minorité avait trouvée en phase 4 venait de la course à la majorité entre copies (phase 5i), et ce que la table mixte de la phase 5i y ajoutait venait du Hard trop généreux. Il ne reste pas grand-chose de l'exploiteur.

## Le tournoi

J'ai rejoué la règle d'entrée avec le Hard recalé comme remplissant, sur la graine 1 comme en phase 5i. Le Hard recalé est environ 1,75 fois plus lent que l'ancien, alors j'ai réduit le tournoi pour qu'il tienne dans la nuit : 100 donnes de 10 manches au lieu de 300, et 10 références à la table mixte au lieu de 15. J'ai écarté l'heuristique, le sniper, l'imitateur, les deux fondamentalistes et la mante, qui perdaient tous plus de 30 $ par manche face à la v4c à la table mixte de la phase 5i. Les intervalles sont donc environ 1,7 fois plus larges qu'en phase 5i.

Face à trois copies d'un même adversaire (gain du candidat, en dollars par manche) :

| Adversaire | v4c, 4 j. | v4c, 5 j. | v4c calme 60 s, 4 j. | v4c calme 60 s, 5 j. |
|---|---|---|---|---|
| heuristique | +44,58 [+42,64 ; +46,52] | +43,63 [+42,06 ; +45,20] | +36,24 [+34,45 ; +38,02] | +36,59 [+35,23 ; +37,94] |
| sniper | +27,91 [+26,54 ; +29,28] | +26,09 [+24,81 ; +27,36] | +26,25 [+24,83 ; +27,66] | +24,59 [+23,28 ; +25,91] |
| bayésien | +26,99 [+25,45 ; +28,53] | +28,11 [+26,61 ; +29,62] | +25,40 [+23,69 ; +27,11] | +24,97 [+23,35 ; +26,58] |
| marginal | +7,67 [+6,75 ; +8,58] | +4,17 [+3,43 ; +4,91] | **-0,06 [-0,97 ; +0,84]** | **-3,44 [-4,21 ; -2,67]** |
| Hard de la phase 5c | +36,57 [+35,03 ; +38,11] | +34,59 [+33,41 ; +35,78] | +39,10 [+37,34 ; +40,85] | +36,76 [+35,54 ; +37,98] |
| Hard recalé | -7,65 [-9,23 ; -6,07] | -4,82 [-6,27 ; -3,38] | +12,12 [+10,36 ; +13,88] | +14,33 [+12,63 ; +16,03] |

À la table mixte (écart référence moins candidat, en dollars par manche ; un écart dont tout l'intervalle est au-dessus de 0 refuse le candidat) :

| Référence | v4c, 4 j. | v4c, 5 j. | v4c calme 60 s, 4 j. | v4c calme 60 s, 5 j. |
|---|---|---|---|---|
| Hard recalé | **+9,86 [+7,64 ; +12,07]** | **+5,64 [+3,73 ; +7,54]** | -16,13 [-18,67 ; -13,59] | -18,35 [-20,60 ; -16,11] |
| bayésien | +0,48 [-2,06 ; +3,02] | -5,76 [-7,65 ; -3,87] | -16,35 [-18,42 ; -14,28] | -20,33 [-22,09 ; -18,57] |
| marginal | -4,25 [-6,06 ; -2,43] | -2,16 [-3,89 ; -0,44] | -12,02 [-14,26 ; -9,78] | -9,42 [-11,34 ; -7,49] |
| v3 | -0,14 [-1,97 ; +1,69] | **+2,26 [+0,45 ; +4,08]** | -9,54 [-11,77 ; -7,32] | -5,55 [-7,80 ; -3,31] |
| v4b | +0,42 [-0,18 ; +1,01] | +0,47 [-0,06 ; +1,00] | -6,86 [-8,18 ; -5,54] | -5,79 [-7,05 ; -4,53] |
| v4c | | | -7,40 [-8,72 ; -6,08] | -5,34 [-6,61 ; -4,07] |
| exploiteur | -5,23 [-6,89 ; -3,57] | -5,46 [-7,17 ; -3,75] | -13,75 [-15,46 ; -12,05] | -13,09 [-14,71 ; -11,48] |
| exploiteur lecteur | **+1,52 [+0,01 ; +3,03]** | **+7,23 [+5,71 ; +8,75]** | -5,77 [-7,87 ; -3,68] | **+4,57 [+2,75 ; +6,39]** |
| vendeur | +0,47 [-1,03 ; +1,97] | **+2,68 [+1,26 ; +4,09]** | -10,50 [-11,84 ; -9,15] | -8,25 [-9,63 ; -6,87] |
| parieur | -0,92 [-3,30 ; +1,47] | -1,77 [-3,80 ; +0,25] | -13,13 [-15,03 ; -11,22] | -15,34 [-17,23 ; -13,45] |

Les verdicts :

- **v4c** : refusée à 4 et à 5 joueurs. Elle bat bien les quatre références du zoo, mais le Hard recalé et l'exploiteur lecteur font mieux qu'elle à la table mixte, et à 5 joueurs la v3 et le vendeur aussi.
- **v4c calme 60 s** : refusée à 4 et à 5 joueurs. À 4 joueurs, seule une chose lui manque : battre nettement le marginal face à ses copies, et elle fait jeu égal. À 5 joueurs, elle perd 3,44 $ par manche face aux copies du marginal, et l'exploiteur lecteur fait mieux qu'elle à la table mixte.

Par rapport à la phase 5i, les chiffres de la v4c face au zoo ne bougent presque pas (+7,67 $ contre +7,75 $ face au marginal à 4 joueurs) : ce sont les mêmes adversaires et le même tirage des donnes, sur moins de donnes. La table mixte change beaucoup. L'exploiteur passe de +10,43 $ à -5,23 $ face à la v4c à 4 joueurs, et le bayésien de +7,13 $ à -5,76 $ à 5 joueurs : les deux exploitations de la phase 5i disparaissent avec le Hard trop généreux. Mais d'autres apparaissent. L'exploiteur lecteur passe de -13,91 $ à +1,52 $, le vendeur de -10,08 $ à +2,68 $ à 5 joueurs. Ces références n'ont pas changé ; c'est la v4c qui gagne moins à une table de Hard recalés, parce qu'elle leur achète trop cher en première minute.

Le bot progresse-t-il ? Non, au sens de la règle d'entrée : aucun candidat ne la passe, et le marginal reste le bot de référence. La v4c qui se tait 60 s est le résultat le plus intéressant de la phase : à une table de Hard recalés, elle gagne environ 20 $ de plus par manche que la v4c, et à la table mixte, aucune des dix références ne fait mieux qu'elle à 4 joueurs. Mais face à des bots qui cotent dès le début, comme le marginal, se taire une minute lui coûte ce qu'elle gagnait. Ces gains sont mesurés contre des bots simulés : ce ne sont pas des gains réels sur figgie.com.

## Limites

Le Hard recalé colle aux vrais bots du site sur la part des offres prises, mais moins bien que l'ancien sur le nombre d'échanges entre Hard. Les deux sont des imitations réglées sur 60 manches d'un seul joueur, Rasmus, face aux bots Hard. Ce que je mesure contre eux n'est pas ce que mes bots feraient sur figgie.com.

La comparaison des offres prises ne porte pas sur les mêmes vendeurs : sur les vraies manches, ce sont les offres du bot de Rasmus et des Hard ; en simulation, celles de mes bots et des Hard simulés. Un Hard pourrait réagir autrement à une offre de l'exploiteur qu'à une offre du bot de Rasmus au même prix. Rien dans les journaux ne permet de le vérifier.

La recalibration ne voit pas tout. Les tranches de prix laissent de côté les offres de vente à plus de 13 $ et celles de la couleur objectif à 6 $ ou moins. Et un réglage qui ne pose aucune offre dans une tranche, sur les 30 manches de la recherche, a un écart infini : c'est le cas de 1964 réglages sur 3000. Ils sont écartés pour manque de données, pas parce qu'ils ressemblent mal au site.

Les parties simples face au Hard recalé jouent toujours au même siège : elles sont plus bruitées que le tournoi.

Tout reste mesuré contre des bots simulés. Ces gains ne sont pas des gains réels sur figgie.com.

## Reproduire

```bash
cd projets/bot-figgie
python3 -m unittest                                                  # les 134 tests, environ 5 s
python3 -m figgie.calibrate --settings 3000 --rounds 30 --keep 10 --lift --out calibration_hard_v2.json
python3 -m figgie.tournoi --site --seed 7 --candidates marginal adaptatif_v4c v4c_calme_60 --rounds 10 --deals 50 \
    --no-tables --opponents --references --mixed exploiteur bayesien --out calibration.json
python3 -m figgie.tournoi --site --candidates adaptatif_v4c v4c_calme_60 --rounds 10 --deals 100 --no-tables \
    --opponents heuristique sniper bayesien marginal hard_simule hard_simule_v2 --references \
    --mixed hard_simule_v2 bayesien marginal adaptatif_v3 adaptatif_v4b adaptatif_v4c exploiteur exploiteur_lecteur \
        vendeur parieur --out tournoi.json
```

La recalibration prend environ 3 min sur 10 cœurs, la calibration 13 min, le tournoi environ 3 h 30. Pour revenir exactement au code de cette phase : `git checkout phase5j-figgie`.
