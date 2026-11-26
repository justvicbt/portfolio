# Phase 5n : le poids de la majorité à l'achat seulement

*English version: [phase5n.en.md](phase5n.en.md)*

En phase 5l, la part de majorité dans la valeur d'une carte a reçu un poids qui monte avec le temps. Ce poids valait à l'achat comme à la vente. Le diagnostic de la 5l a montré le prix de ce choix : à 5 joueurs, le bot vendait ses cartes objectif en début de manche, parce qu'une carte objectif ne valait plus pour lui que 10 $ fois la chance que sa couleur soit l'objectif. Les joueurs qui comptent la majorité en entier les lui rachetaient. Cette phase garde le poids à l'achat, où il empêche de surpayer les cartes de la première minute, et le retire à la vente.

Résultat : le candidat passe la règle d'entrée à 4 et à 5 joueurs, au tournoi réduit comme au tournoi complet à 300 donnes. Aucun candidat n'y était arrivé depuis que la règle se joue à la table mixte, en phase 5i. Il est promu et remplace le marginal comme bot de référence. Deux réserves : à 5 joueurs, il ne fait que jeu égal avec l'exploiteur lecteur, et il gagne moins que l'ancienne version face aux marginaux. Ces gains sont mesurés contre des bots simulés, pas sur le site.

## Le changement

`marginal_values` reçoit un paramètre `weight_sell`. À `False`, la valeur d'achat garde la part de majorité pondérée par le temps, et la valeur de vente compte la majorité en entier, comme avant la phase 5l. Le nouveau candidat, `v4c_achat`, est la v4c avec ce réglage. Il n'est pas réentraîné : il joue avec les réglages de la v4c, que la phase 5m a réappris sur le code corrigé.

Deux seams, écrits en TDD sur une même main et un même tirage :
- avec le poids à l'achat seulement, chaque valeur de vente est exactement celle de la valeur sans poids ;
- chaque valeur d'achat est exactement celle de la phase 5l, avec le poids des deux côtés. Le test vérifie aussi que, dans ce cas, le poids change bien au moins une valeur de vente : sinon le premier seam ne pourrait rien voir.

Les deux tests échouaient avant le code. J'ai ensuite vérifié qu'ils attrapent deux erreurs volontaires : remettre le poids à la vente, et le retirer à l'achat.

## Choisir T

Le poids reste min(1, t / T) ^ 0,5, avec k = 0,5 comme en 5l. J'ai essayé T = 60, 120 et 240 secondes. Cette fois, j'ai mesuré à 4 et à 5 joueurs, puisque c'est à 5 joueurs que la 5l avait échoué.

Le critère, fixé avant de lancer : la moyenne de quatre gains (face à trois Hard recalés et face à trois marginaux, à 4 et à 5 joueurs), moins l'écart de la v4c qui se tait à la table mixte à 5 joueurs. C'était la référence qui refusait le bot en phase 5m. Graine 9 (jamais la graine 1 du tournoi), 100 donnes dupliquées, parties de 10 manches, règle du site, réglages de la v4c pour tous.

| Bot | 3 Hard recalés, 4 j. | 3 Hard recalés, 5 j. | 3 marginaux, 4 j. | 3 marginaux, 5 j. | v4c calme, table mixte, 5 j. | score |
|---|---|---|---|---|---|---|
| v4c | -5,83 [-7,62 ; -4,05] | -4,35 [-5,93 ; -2,77] | +8,45 [+7,63 ; +9,28] | +4,90 [+3,98 ; +5,83] | +5,78 [+4,74 ; +6,83] | -4,99 |
| poids des deux côtés, T = 120 s (5l) | +16,67 [+14,89 ; +18,45] | +14,80 [+13,32 ; +16,27] | +12,80 [+11,65 ; +13,94] | +10,31 [+9,31 ; +11,30] | +1,84 [+0,79 ; +2,90] | +11,80 |
| achat seul, T = 60 s | +9,10 [+7,30 ; +10,90] | +14,81 [+13,09 ; +16,53] | +10,85 [+9,81 ; +11,90] | +6,86 [+5,95 ; +7,76] | +1,81 [+0,69 ; +2,93] | +8,60 |
| achat seul, T = 120 s | +16,08 [+14,29 ; +17,87] | +17,65 [+16,42 ; +18,88] | +11,80 [+10,78 ; +12,82] | +7,32 [+6,47 ; +8,16] | +0,65 [-0,34 ; +1,63] | +12,57 |
| **achat seul, T = 240 s** | **+17,94 [+16,35 ; +19,53]** | **+15,25 [+13,84 ; +16,66]** | **+13,61 [+12,54 ; +14,68]** | **+9,21 [+8,37 ; +10,05]** | **-0,00 [-0,98 ; +0,97]** | **+14,01** |

Le critère retient T = 240 s. C'est aussi le seul point où la v4c qui se tait ne fait plus mieux que le candidat à la table mixte : l'écart est nul, avec un intervalle centré sur 0. Avec T = 240 s, la majorité ne compte à l'achat qu'à moitié au bout d'une minute, à 71 % au bout de deux, et en entier seulement à la cloche.

Le poids à l'achat seul ne gagne pas partout. À 5 joueurs face aux marginaux, le poids des deux côtés fait mieux (+10,31 $ contre +9,21 $). C'est l'écart face à la v4c qui se tait qui fait la différence de score.

## Le tournoi réduit

Même format qu'en phase 5m : graine 1, 100 donnes de 10 manches, règle du site, avec le Hard recalé comme remplissant de la table mixte. J'ai ajouté une 13e référence, la v4c au temps de la phase 5l, pour mesurer le candidat directement face au bot qu'il veut remplacer. Cette fois, seul le candidat change : aucun autre bot ne lit le nouveau paramètre, donc tous les adversaires jouent exactement comme en phase 5m. L'écart entre les deux colonnes vient du candidat.

Face à trois copies d'un même adversaire (gain du candidat, en dollars par manche) :

| Adversaire | 5n, 4 j. | 5n, 5 j. | 5m, 4 j. | 5m, 5 j. |
|---|---|---|---|---|
| heuristique | +42,70 [+40,62 ; +44,77] | +38,32 [+36,73 ; +39,92] | +42,48 | +37,54 |
| sniper | +32,67 [+31,24 ; +34,10] | +29,94 [+28,73 ; +31,15] | +33,81 | +31,51 |
| bayésien | +25,89 [+24,07 ; +27,72] | +25,48 [+23,86 ; +27,10] | +24,31 | +23,41 |
| marginal | +13,31 [+12,43 ; +14,19] | **+8,92 [+8,05 ; +9,79]** | +12,19 | **+12,40** |
| Hard de la phase 5c | +43,00 [+41,59 ; +44,41] | +38,29 [+37,13 ; +39,44] | +38,24 | +34,40 |
| Hard recalé | +17,58 [+16,00 ; +19,16] | +15,91 [+14,55 ; +17,27] | +15,26 | +13,13 |

À la table mixte (écart référence moins candidat, en dollars par manche ; un écart dont tout l'intervalle est au-dessus de 0 refuse le candidat) :

| Référence | 5n, 4 j. | 5n, 5 j. | 5m, 4 j. | 5m, 5 j. |
|---|---|---|---|---|
| Hard recalé | -23,45 [-25,69 ; -21,21] | -20,31 [-22,05 ; -18,56] | -20,61 | -16,28 |
| bayésien | -29,85 [-31,65 ; -28,04] | -22,49 [-23,98 ; -21,01] | -21,94 | -18,97 |
| marginal | -18,88 [-20,75 ; -17,02] | -13,42 [-15,28 ; -11,55] | -14,67 | -10,54 |
| v3 | -13,45 [-15,46 ; -11,44] | -10,22 [-12,23 ; -8,21] | -9,96 | -6,30 |
| v4b | -13,25 [-14,74 ; -11,75] | -7,53 [-8,96 ; -6,10] | -8,36 | -1,68 |
| v4c | -15,64 [-17,03 ; -14,26] | -8,82 [-10,18 ; -7,46] | -8,08 | -2,64 |
| v4c calme 60 s | -3,85 [-5,12 ; -2,57] | -1,85 [-3,02 ; -0,67] | -1,09 | **+3,05** |
| v4c vendeuse (5k) | -5,80 [-6,83 ; -4,77] | -3,21 [-4,14 ; -2,28] | -3,07 | +0,02 |
| exploiteur | -19,24 [-20,85 ; -17,64] | -15,05 [-16,30 ; -13,80] | -17,24 | -15,90 |
| exploiteur lecteur | -10,99 [-13,00 ; -8,97] | +0,34 [-1,08 ; +1,75] | -6,64 | +0,22 |
| vendeur | -17,65 [-18,92 ; -16,38] | -12,66 [-13,75 ; -11,57] | -15,42 | -10,25 |
| parieur | -17,11 [-18,89 ; -15,33] | -16,02 [-17,47 ; -14,56] | -13,02 | -12,77 |
| v4c au temps (5l) | -4,45 [-5,56 ; -3,33] | -3,29 [-4,15 ; -2,43] | | |

Le candidat passe la règle d'entrée à 4 et à 5 joueurs. C'est la première fois qu'un candidat passe aux deux tailles de table depuis que la règle d'entrée se joue à la table mixte, en phase 5i. La v4c qui se tait, qui refusait la v4c au temps à 5 joueurs, finit maintenant 1,85 $ derrière le candidat, avec un intervalle entièrement sous 0. Face à la v4c au temps elle-même, le candidat gagne 4,45 $ par manche à 4 joueurs et 3,29 $ à 5 joueurs.

Deux réserves. L'exploiteur lecteur fait toujours jeu égal à 5 joueurs (+0,34 $, avec un intervalle qui contient 0) : la règle passe parce qu'elle ne refuse que ce qui est franchement devant, pas parce que le candidat le bat. Et face à trois marginaux à 5 joueurs, le candidat perd plus de 3 $ par manche par rapport à la phase 5m (+8,92 $ contre +12,40 $, des intervalles qui ne se touchent pas). La grille l'annonçait déjà : à 5 joueurs face aux marginaux, garder le poids à la vente rapporte plus. Je n'ai pas vérifié d'où vient cette perte.

## Le tournoi complet

Comme le candidat passait aux deux tailles, j'ai lancé le tournoi complet : graine 1, 300 donnes de 10 manches, et toutes les références à la table mixte, celles de la phase 5i plus le Hard recalé, la v4c, la v4c qui se tait, la v4c vendeuse et la v4c au temps. Le dernier tournoi complet datait de la phase 5i, sur un autre code : je ne compare donc pas ses chiffres à ceux-ci.

Face à trois copies d'un même adversaire (gain du candidat, en dollars par manche) :

| Adversaire | 4 j. | 5 j. |
|---|---|---|
| heuristique | +41,39 [+40,30 ; +42,48] | +39,23 [+38,33 ; +40,12] |
| sniper | +32,24 [+31,43 ; +33,06] | +30,05 [+29,39 ; +30,71] |
| bayésien | +25,73 [+24,71 ; +26,75] | +25,45 [+24,48 ; +26,41] |
| marginal | +13,00 [+12,47 ; +13,53] | +9,16 [+8,66 ; +9,66] |
| Hard de la phase 5c | +41,71 [+40,86 ; +42,56] | +38,00 [+37,35 ; +38,66] |
| Hard recalé | +17,83 [+16,91 ; +18,75] | +16,55 [+15,75 ; +17,34] |

À la table mixte (écart référence moins candidat, en dollars par manche) :

| Référence | 4 j. | 5 j. |
|---|---|---|
| Hard de la phase 5c | -84,61 [-85,97 ; -83,25] | -81,39 [-82,48 ; -80,30] |
| heuristique | -72,11 [-73,44 ; -70,77] | -58,62 [-59,81 ; -57,44] |
| imitateur | -31,80 [-33,21 ; -30,39] | -38,47 [-39,74 ; -37,20] |
| fondamentaliste (r = 3,5) | -35,57 [-36,61 ; -34,52] | -29,36 [-30,20 ; -28,52] |
| sniper | -33,71 [-34,67 ; -32,75] | -26,58 [-27,43 ; -25,73] |
| bayésien | -30,48 [-31,55 ; -29,41] | -22,69 [-23,57 ; -21,81] |
| mante | -25,36 [-26,24 ; -24,47] | -22,69 [-23,46 ; -21,92] |
| fondamentaliste (r = 1,7) | -25,43 [-26,63 ; -24,24] | -20,91 [-21,76 ; -20,07] |
| Hard recalé | -23,66 [-24,96 ; -22,37] | -20,92 [-21,95 ; -19,89] |
| exploiteur | -19,44 [-20,38 ; -18,51] | -15,21 [-15,96 ; -14,45] |
| marginal | -18,54 [-19,65 ; -17,43] | -14,42 [-15,42 ; -13,43] |
| parieur | -16,78 [-17,76 ; -15,80] | -16,44 [-17,24 ; -15,64] |
| vendeur | -17,62 [-18,35 ; -16,90] | -13,09 [-13,74 ; -12,44] |
| v3 | -14,29 [-15,46 ; -13,12] | -10,26 [-11,31 ; -9,21] |
| v4c | -13,75 [-14,59 ; -12,92] | -9,05 [-9,80 ; -8,31] |
| v4b | -12,04 [-12,94 ; -11,14] | -7,61 [-8,40 ; -6,82] |
| v4c vendeuse (5k) | -5,97 [-6,57 ; -5,36] | -3,70 [-4,21 ; -3,19] |
| v4c au temps (5l) | -3,90 [-4,49 ; -3,30] | -4,25 [-4,76 ; -3,74] |
| v4c calme 60 s | -3,63 [-4,30 ; -2,96] | -1,19 [-1,85 ; -0,53] |
| exploiteur lecteur | -10,10 [-11,20 ; -9,00] | -0,10 [-0,95 ; +0,74] |

Le candidat passe la règle d'entrée à 4 et à 5 joueurs, avec trois fois plus de donnes et sept références de plus. À 4 joueurs, il finit devant les 20 références, avec un intervalle entièrement sous 0. À 5 joueurs, il finit devant 19 d'entre elles. L'exploiteur lecteur fait jeu égal avec lui : -0,10 $, avec un intervalle qui contient 0. Les chiffres du tournoi réduit tiennent : la v4c qui se tait reste derrière, et la perte face aux marginaux à 5 joueurs aussi (+9,16 $ par manche).

## Le bot progresse-t-il ?

Oui, au sens de la règle d'entrée. Pour la première fois depuis que la règle se joue à la table mixte, un candidat la passe aux deux tailles, au tournoi réduit comme au tournoi complet. Face à la v4c au temps de la phase 5l, dont il ne diffère que par la vente, il gagne 3,90 $ par manche à 4 joueurs et 4,25 $ à 5. Face aux Hard recalés, le plus proche des bots du site que j'aie, il gagne 2 à 3 $ de plus par manche que la v4c au temps.

Je le promeus donc : `v4c_achat` remplace le marginal comme bot de référence. Ce n'est pas un bot inexploitable. Il fait seulement jeu égal avec l'exploiteur lecteur à 5 joueurs, et il gagne moins que la v4c au temps face aux marginaux à 5 joueurs. La phase suivante cherchera des exploiteurs contre lui.

Ces gains sont mesurés contre des bots simulés : ce ne sont pas des gains réels sur figgie.com.

## Limites

T a été choisi sur la graine 9 parmi trois valeurs seulement, avec k gardé à 0,5. Une valeur plus grande que 240 s n'a pas été essayée, alors que le score montait encore de 120 à 240 s.

Le candidat n'est pas réentraîné : il joue avec les réglages appris par la v4c, dont la valeur pondère aussi la vente. Des réglages appris avec la nouvelle valeur pourraient être différents.

La recherche automatique d'exploiteurs n'a pas été relancée depuis la phase 5b. La règle d'entrée ne teste que les références que j'ai écrites ou reprises : un adversaire taillé contre ce bot pourrait le battre.

Je n'ai pas vérifié pourquoi le candidat gagne moins face aux marginaux à 5 joueurs.

Tout reste mesuré contre des bots simulés. Ces gains ne sont pas des gains réels sur figgie.com.

## Reproduire

```bash
cd projets/bot-figgie
python3 -m unittest                                                  # les 144 tests, environ 7 s
python3 -m figgie.tournoi --site --candidates v4c_achat --rounds 10 --deals 100 --no-tables \
    --opponents heuristique sniper bayesien marginal hard_simule hard_simule_v2 --references \
    --mixed hard_simule_v2 bayesien marginal adaptatif_v3 adaptatif_v4b adaptatif_v4c v4c_calme_60 v4c_vente_60 \
        exploiteur exploiteur_lecteur vendeur parieur v4c_temps --out tournoi.json
python3 -m figgie.tournoi --site --candidates v4c_achat --rounds 10 --deals 300 --no-tables \
    --opponents heuristique sniper bayesien marginal hard_simule hard_simule_v2 --references \
    --mixed hard_simule heuristique sniper bayesien marginal adaptatif_v3 adaptatif_v4b exploiteur \
        exploiteur_lecteur imitateur fondamentaliste fondamentaliste_35 vendeur mante parieur \
        hard_simule_v2 adaptatif_v4c v4c_calme_60 v4c_vente_60 v4c_temps --out tournoi_complet.json
```

Sur 10 cœurs, le tournoi réduit a pris 2 h 24 et le tournoi complet 11 h 32. La grille qui a choisi T est un script hors du dépôt ; sa sortie est dans `resultats/phase5n/grille_graine9.txt`. Pour revenir exactement au code de cette phase : `git checkout phase5n-figgie`.
