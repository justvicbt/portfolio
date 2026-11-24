# Phase 5k : ne rien acheter la première minute

*English version: [phase5k.en.md](phase5k.en.md)*

La phase 5j a laissé deux bots, chacun bon d'un côté. La v4c bat le marginal face à ses copies, mais perd face à trois Hard recalés : elle leur achète trop cher en première minute. La v4c qui se tait pendant la première minute gagne face aux Hard recalés, mais ne bat plus le marginal. Cette phase cherche ce que la v4c fait de travers en première minute, et essaie de n'enlever que ça.

Au tournoi, la v4c vendeuse bat les quatre références du zoo et le Hard recalé, à 4 comme à 5 joueurs. Mais elle est refusée. À la table mixte, la v4c qui se tait fait un peu mieux qu'elle (+1,81 $ par manche à 4 joueurs, +1,57 $ à 5), et l'exploiteur lecteur aussi à 5 joueurs (+3,43 $). Aucun bot n'est promu. C'est pourtant le candidat qui passe le plus près de la règle d'entrée depuis qu'elle existe.

## Ce que la v4c achète en première minute

J'ai fait jouer la v4c seule face à trois Hard recalés, puis face à trois marginaux, sur 40 parties de 10 manches, et j'ai noté chaque fois qu'elle prend une offre de vente : le prix, la valeur qu'elle donne à la carte, et la probabilité qu'elle donne à la couleur d'être l'objectif. Pour la première minute :

| | face aux Hard recalés, hors objectif | face aux Hard recalés, objectif | face aux marginaux, hors objectif | face aux marginaux, objectif |
|---|---|---|---|---|
| prises par manche | 1,02 | 0,36 | 0,82 | 0,26 |
| prix payé | 9,63 $ | 12,28 $ | 11,30 $ | 12,52 $ |
| valeur qu'elle donne à la carte | 13,56 $ | 16,50 $ | 16,25 $ | 17,66 $ |
| probabilité d'objectif qu'elle donne à la couleur | 24 % | 30 % | 30 % | 34 % |

En première minute, la v4c ne sait pas encore quelle couleur est l'objectif : elle donne à peu près la même probabilité à la bonne couleur et aux autres. Comme trois couleurs sur quatre ne sont pas l'objectif, trois de ses achats sur quatre portent sur des cartes qui finiront à 0 $.

Elle les paie pourtant plus de 9 $. Une carte objectif vaut 10 $ à la fin, donc avec 25 % de chances, la carte elle-même vaut environ 2,50 $. Le reste de sa valeur, plus de 10 $, vient de la majorité. Le bot marginal, dont la v4c hérite, calcule ce qu'une carte de plus lui rapporterait à la cloche si plus personne n'échangeait ensuite. Avec trois minutes de marché encore devant elle, c'est une valeur bien trop haute.

## Ne rien acheter, mais vendre

L'idée est de garder ce que la v4c fait de bien en première minute, ses ventes, et de retirer ses achats. J'ai comparé cette version à la v4c et à la v4c qui se tait, sur les mêmes 40 parties simples, toujours au même siège. Gain par manche :

| Bot | face à 3 Hard recalés | face à 3 marginaux |
|---|---|---|
| v4c | -9,18 | +3,74 |
| v4c qui se tait 60 s (phase 5g) | +12,56 | -3,42 |
| v4c qui n'achète rien pendant 60 s | +8,15 | +3,33 |

Ne rien acheter pendant la première minute, tout en continuant à vendre, garde une bonne part de ce que la v4c qui se tait gagne face aux Hard, et presque tout ce que la v4c gagne face aux marginaux.

La v4c qui se tait perdait face aux marginaux pour une raison simple : elle perdait aussi ses ventes de la première minute, qui rapportent 11,49 $ par manche à la v4c face à eux. La version qui n'achète rien en tire même 14,40 $ : elle ne passe plus aucun tour à acheter, et vend davantage. Et quand la v4c qui se tait se met à jouer, à 60 s, elle refait les mêmes achats : 1,49 carte par manche autour de 9,40 $, pour une perte de 10,40 $.

## La v4c vendeuse

La nouvelle version s'appelle `v4c_vente_60`. C'est la v4c, sans réentraînement, pour qui une carte ne vaut rien à l'achat pendant les 60 premières secondes de chaque manche. Avec une valeur de 0 $, elle ne prend aucune offre de vente et ne pose aucune offre d'achat. Tout le reste ne change pas : elle vend, elle cote à la vente, elle retire ses cotations, et elle choisit son réglage comme la v4c.

Ma première version faisait autrement, et la relecture du code y a trouvé un défaut. Elle laissait la v4c choisir son action, puis l'annulait si c'était un achat. Or la v4c ne choisit qu'une action par tour, et regarde les achats avant les ventes. Chaque fois qu'elle voulait acheter, ma version ne faisait donc rien du tout, au lieu de vendre. Elle vendait moins que la v4c, le contraire de ce que je voulais. Le premier tournoi et mes deux vérifications sur les graines 7 et 11 portaient sur cette version. J'ai corrigé, puis tout relancé.

Le seam est son comportement dans une partie jouée avec la règle du site : aucun achat ni offre d'achat avant 60 s, au moins autant de ventes et d'offres de vente avant 60 s que la v4c à la même table, et le même choix de réglage que la v4c. La condition « au moins autant que la v4c » vient de la relecture. Ma première version la ratait (55 ventes et offres de vente contre 67 pour la v4c), et le test l'a bien vu avant que je corrige. Pour vérifier que le test peut échouer, je l'ai aussi faussé en laissant passer les achats : il échoue. Le test ne vérifie pas qu'après 60 s, elle joue exactement comme la v4c.

## Le tournoi

Même format que la phase 5j : graine 1, 100 donnes de 10 manches, le Hard recalé comme remplissant de la table mixte. J'ai ajouté une onzième référence à la table mixte, la v4c qui se tait 60 s : sur la graine 7, elle faisait mieux que la première version de la v4c vendeuse à 5 joueurs, et la laisser de côté aurait rendu la règle plus facile à passer. Comme les donnes sont les mêmes qu'en phase 5j, les chiffres de la v4c et de la v4c qui se tait se comparent directement.

Face à trois copies d'un même adversaire (gain du candidat, en dollars par manche) :

| Adversaire | v4c vendeuse, 4 j. | v4c vendeuse, 5 j. | v4c, 4 j. (5j) | v4c calme 60 s, 4 j. (5j) |
|---|---|---|---|---|
| heuristique | +36,47 [+34,57 ; +38,38] | +34,33 [+32,98 ; +35,68] | +44,58 | +36,24 |
| sniper | +25,86 [+24,53 ; +27,18] | +24,48 [+23,32 ; +25,63] | +27,91 | +26,25 |
| bayésien | +23,08 [+21,33 ; +24,84] | +22,03 [+20,40 ; +23,65] | +26,99 | +25,40 |
| marginal | +7,26 [+6,30 ; +8,23] | +4,80 [+3,97 ; +5,62] | +7,67 | -0,06 |
| Hard de la phase 5c | +36,96 [+35,39 ; +38,54] | +33,53 [+32,39 ; +34,67] | +36,57 | +39,10 |
| Hard recalé | +10,06 [+8,31 ; +11,81] | +12,14 [+10,67 ; +13,60] | -7,65 | +12,12 |

À la table mixte (écart référence moins candidat, en dollars par manche ; un écart dont tout l'intervalle est au-dessus de 0 refuse le candidat) :

| Référence | v4c vendeuse, 4 j. | v4c vendeuse, 5 j. |
|---|---|---|
| Hard recalé | -13,44 [-15,92 ; -10,96] | -15,34 [-17,22 ; -13,47] |
| bayésien | -13,78 [-15,73 ; -11,82] | -15,45 [-17,18 ; -13,72] |
| marginal | -13,90 [-15,55 ; -12,26] | -12,21 [-13,78 ; -10,63] |
| v3 | -11,90 [-13,81 ; -9,98] | -8,79 [-10,48 ; -7,10] |
| v4b | -8,67 [-10,05 ; -7,30] | -5,29 [-6,50 ; -4,07] |
| v4c | -8,85 [-10,30 ; -7,41] | -5,79 [-7,04 ; -4,54] |
| v4c calme 60 s | **+1,81 [+0,69 ; +2,92]** | **+1,57 [+0,61 ; +2,52]** |
| exploiteur | -13,27 [-14,84 ; -11,70] | -12,33 [-13,70 ; -10,97] |
| exploiteur lecteur | -4,22 [-5,91 ; -2,53] | **+3,43 [+1,80 ; +5,06]** |
| vendeur | -8,38 [-9,71 ; -7,05] | -7,17 [-8,47 ; -5,88] |
| parieur | -14,21 [-16,09 ; -12,33] | -14,26 [-15,80 ; -12,73] |

La v4c vendeuse fait ce que j'en attendais face au zoo. Elle garde presque tout ce que la v4c gagne face au marginal (+7,26 $ contre +7,67 $ à 4 joueurs), et une bonne part de ce que la v4c qui se tait gagne face au Hard recalé (+10,06 $ contre +12,12 $). En échange, elle gagne 8 $ de moins que la v4c face à l'heuristique, et 4 $ de moins face au bayésien.

Ma première version, celle qui perdait des tours, était refusée par les mêmes références, avec des écarts proches : +1,11 $ et +1,81 $ pour la v4c qui se tait, +1,82 $ pour l'exploiteur lecteur à 5 joueurs. La correction gagne un peu face au zoo (par exemple +7,26 $ au lieu de +6,91 $ face au marginal à 4 joueurs), et perd un peu face à l'exploiteur lecteur à 5 joueurs. Ces différences restent de l'ordre de la largeur des intervalles.

## Pourquoi la v4c qui se tait fait mieux

J'ai décomposé les gains de la v4c vendeuse et de la v4c qui se tait face à trois Hard recalés, sur 40 parties simples, minute par minute. Deux choses ressortent.

En première minute, la v4c vendeuse vend aussi des cartes objectif : 0,41 par manche, à 7,33 $ en moyenne. Chaque vente lui coûte un peu d'argent (1,09 $ par manche en tout), et surtout une carte pour la majorité. Elle gagne la majorité dans 47 % des manches, contre 55 % pour la v4c qui se tait, et sa part de majorité rapporte 9,33 $ de moins par manche. Ses ventes de cartes hors objectif en première minute ne rapportent que 2,43 $ par manche.

En deuxième minute, les deux refont exactement l'erreur que la phase 5k voulait éviter : environ 1,5 carte hors objectif par manche, à 7,51 $ pour la v4c vendeuse et 9,40 $ pour la v4c qui se tait, pour une perte de 10 à 12 $ par manche. Retarder les achats ne suffit pas. La valeur qui pousse à acheter est toujours trop haute une fois la première minute passée.

## Ce que l'exploiteur lecteur lui prend à 5 joueurs

J'ai fait jouer l'exploiteur lecteur, la v4c vendeuse et trois Hard recalés, sur 40 parties de 10 manches, dans les deux ordres des sièges. Pour chaque échange, je compte ce que le vendeur gagne sur l'acheteur : le prix moins la valeur finale de la carte (10 $ si elle est de la couleur objectif, 0 $ sinon). Ce qui reste du gain de chacun, ce sont ses cartes objectif de départ, sa part de la majorité, moins la mise.

| Ordre des sièges | gain de l'exploiteur lecteur | gain de la v4c vendeuse | écart |
|---|---|---|---|
| exploiteur lecteur d'abord | +2,21 | +1,08 | +1,13 |
| v4c vendeuse d'abord | +7,07 | -1,51 | +8,58 |
| moyenne | +4,64 | -0,22 | +4,86 |

L'exploiteur lecteur passe devant dans les deux ordres, et la moyenne est proche de l'écart du tournoi (+3,43 $). Pourtant, la v4c vendeuse gagne sur chaque échange avec lui : 5,48 $ par manche en moyenne. Elle perd aussi moins que lui face aux Hard (6,19 $ contre 11,04 $). Tout se joue dans le reste : sur la moyenne des deux ordres, les mains de départ s'annulent, et ce reste rapporte 21,15 $ par manche à l'exploiteur lecteur contre 0,49 $ à la v4c vendeuse. Autrement dit, l'exploiteur lecteur paie trop cher ses cartes, mais il ramasse la majorité. La v4c vendeuse, qui n'achète rien pendant la première minute et vend même des cartes objectif, la lui laisse.

C'est le même défaut que face aux Hard recalés, vu d'un autre côté : la v4c vendeuse gagne ses échanges, mais perd la majorité.

Le bot progresse-t-il ? Pas au sens de la règle d'entrée : la v4c vendeuse est refusée, et le marginal reste le bot de référence. Mais elle passe plus près que les candidats d'avant. Son pire écart à la table mixte est de +3,43 $ par manche, contre +9,86 $ pour la v4c et +4,57 $ pour la v4c qui se tait en phase 5j, sur les mêmes donnes. Et elle bat à la fois le marginal et le Hard recalé, à 4 comme à 5 joueurs, ce que ni la v4c ni la v4c qui se tait ne faisaient en phase 5j. Ces gains sont mesurés contre des bots simulés : ce ne sont pas des gains réels sur figgie.com.

Comme elle est refusée à 4 joueurs, je n'ai pas lancé le tournoi complet au format de la phase 5i (300 donnes, toutes les références) que j'avais prévu en cas de succès.

## Limites

Le diagnostic des achats porte sur des parties simples, toujours au même siège, sans intervalle de confiance. Seule la v4c vendeuse a été mesurée en donnes dupliquées, au tournoi. Ces parties simples et les deux diagnostics sont faits avec des scripts hors dépôt.

La valeur que la v4c donne à une carte en première minute est trop haute, et je ne la corrige pas : je l'empêche seulement d'acheter. Une correction de la valeur elle-même, qui tiendrait compte du temps qui reste, serait plus propre, et coûterait un réentraînement.

Le tournoi est réduit comme celui de la phase 5j : 100 donnes au lieu de 300, et une partie des références. Les intervalles sont environ 1,7 fois plus larges qu'en phase 5i.

Tout reste mesuré contre des bots simulés. Ces gains ne sont pas des gains réels sur figgie.com.

## Reproduire

```bash
cd projets/bot-figgie
python3 -m unittest                                                  # les 135 tests, environ 5 s
python3 -m figgie.tournoi --site --candidates v4c_vente_60 --rounds 10 --deals 100 --no-tables \
    --opponents heuristique sniper bayesien marginal hard_simule hard_simule_v2 --references \
    --mixed hard_simule_v2 bayesien marginal adaptatif_v3 adaptatif_v4b adaptatif_v4c v4c_calme_60 exploiteur \
        exploiteur_lecteur vendeur parieur --out tournoi.json
```

Le tournoi prend environ 2 h 05 sur 10 cœurs. Pour revenir exactement au code de cette phase : `git checkout phase5k-figgie`.
