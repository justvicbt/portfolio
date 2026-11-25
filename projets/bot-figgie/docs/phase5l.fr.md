# Phase 5l : une valeur de carte qui tient compte du temps restant

*English version: [phase5l.en.md](phase5l.en.md)*

La phase 5k a contourné un défaut de la v4c sans le corriger. En première minute, la v4c donne 13,50 $ à 16 $ à une carte dont elle croit la couleur objectif à 25 ou 30 %. La carte elle-même vaut environ 2,50 $ ; le reste vient de la majorité, que la valeur du bot marginal compte comme si plus personne n'échangeait ensuite. La 5k a interdit d'acheter pendant 60 s. Le bot y gagnait ses échanges, mais perdait la majorité. Cette phase corrige la valeur elle-même.

Au tournoi, la nouvelle v4c est le meilleur bot du projet face au zoo : à 4 joueurs, elle gagne 9,74 $ par manche face au marginal et 15,18 $ face au Hard recalé, contre 7,26 $ et 10,06 $ pour la v4c vendeuse de la phase 5k. C'est aussi le premier candidat qui passe la règle d'entrée à 4 joueurs. Mais elle est refusée à 5 joueurs : à la table mixte, la v4c qui se tait la première minute fait 2,46 $ de mieux qu'elle par manche, et l'exploiteur lecteur 1,66 $. Aucun bot n'est promu.

## Séparer la carte de la majorité

Quand une carte objectif change de main, mon gain final change pour deux raisons. La carte elle-même vaut 10 $. Et ma part du reste du pot peut changer : une carte de plus peut me donner la majorité, une carte de moins peut me la faire perdre. Jusqu'ici, la valeur comptait les deux en entier, quel que soit le moment de la manche.

Or au début de la manche, la majorité est loin d'être jouée : il reste trois ou quatre minutes d'échanges, et une carte achetée maintenant ne garantit rien à la cloche. Je garde donc la part de la carte en entier, et je multiplie la part de majorité par un poids qui monte avec le temps :

w(t) = min(1, t / T) ^ k

Au début de la manche, w vaut 0 : une carte objectif vaut 10 $ fois la probabilité que sa couleur soit l'objectif. À partir de T secondes, w vaut 1, et la valeur redevient celle d'aujourd'hui. k règle la vitesse de la montée.

Le poids compte à l'achat comme à la vente. C'est un choix qui a un coût possible : en début de manche, une carte objectif vaut aussi moins cher à la vente, et la 5k a montré que vendre ses cartes objectif tôt fait perdre la majorité. Le tournoi dira si ce coût l'emporte.

Pour ne pas refaire le Monte Carlo à chaque tour, le poids est arrondi au vingtième : la valeur n'est recalculée qu'une vingtaine de fois de plus par manche.

Les seams, écrits en TDD :
- avec un poids de 0 et une couleur objectif connue à coup sûr, une carte de cette couleur vaut exactement 10 $ à l'achat comme à la vente, et une carte des autres couleurs 0 $. Avec la majorité, elle vaut plus de 10 $. Le test attrape une majorité mal retirée (je l'ai faussé en multipliant tout le gain par le poids : il échoue) ;
- avec un poids de 1, les valeurs sont celles d'aujourd'hui, à graine égale. Le test attrape un tirage aléatoire qui changerait avec le poids. La relecture du code y a trouvé un défaut : ma première version comparait deux appels avec un poids de 1, qui passaient tous les deux par le raccourci du poids 1, et ne pouvait donc pas voir un tirage qui dépend du poids. Je prends maintenant un poids juste sous 1, et le test échoue quand j'ajoute un tirage de plus dès que le poids n'est pas 1. Les bots existants, eux, passent toujours par le raccourci : ils gardent exactement leurs résultats, et le test de référence du moteur ne bouge pas ;
- sous la règle du site, le bot joue à chaque manche le réglage que donne son modèle réentraîné, lu directement dans le fichier du modèle. Ma première version du test comparait le bot à sa propre méthode de choix : elle passait même quand je cassais ce choix. Je l'ai réécrite, et elle échoue maintenant si le bot garde son réglage de départ, ou s'il lit le modèle de la v4c.

## Choisir T et k

J'ai fixé le critère avant de lancer : la plus haute moyenne entre le gain face à trois Hard recalés et le gain face à trois marginaux. Graine 9 (jamais la graine 1 du tournoi), 100 donnes dupliquées, parties de 10 manches à 4 joueurs, règle du site, avec les réglages de la v4c sans réentraînement :

| Bot | face à 3 Hard recalés | face à 3 marginaux | moyenne |
|---|---|---|---|
| v4c | -6,76 [-8,41 ; -5,11] | +8,50 [+7,58 ; +9,42] | +0,87 |
| v4c vendeuse (5k) | +7,51 [+5,86 ; +9,16] | +7,76 [+6,78 ; +8,74] | +7,63 |
| T = 60 s, k = 0,5 | +12,93 [+11,17 ; +14,70] | +9,15 [+8,16 ; +10,14] | +11,04 |
| T = 60 s, k = 1 | +13,04 [+11,51 ; +14,56] | +8,96 [+7,96 ; +9,96] | +11,00 |
| T = 60 s, k = 2 | +7,64 [+6,14 ; +9,14] | +9,18 [+8,14 ; +10,22] | +8,41 |
| T = 120 s, k = 0,5 | **+15,52 [+13,83 ; +17,21]** | **+10,80 [+9,83 ; +11,77]** | **+13,16** |
| T = 120 s, k = 1 | +10,53 [+9,02 ; +12,03] | +10,09 [+9,12 ; +11,07] | +10,31 |
| T = 120 s, k = 2 | +5,84 [+4,46 ; +7,22] | +10,77 [+9,69 ; +11,85] | +8,31 |
| T = 240 s, k = 0,5 | +13,46 [+11,89 ; +15,03] | +12,25 [+11,15 ; +13,34] | +12,85 |
| T = 240 s, k = 1 | +5,77 [+4,46 ; +7,08] | +12,30 [+11,25 ; +13,35] | +9,03 |
| T = 240 s, k = 2 | -0,70 [-1,83 ; +0,42] | +13,53 [+12,50 ; +14,55] | +6,41 |

Les neuf points battent la v4c, face aux Hard recalés comme face aux marginaux. Plus la majorité revient tard (T grand, k grand), mieux le bot joue face aux marginaux, et moins bien face aux Hard recalés. Le point retenu, T = 120 s et k = 0,5, donne une majorité qui compte déjà à moitié au bout de 30 s, à 71 % au bout d'une minute, et en entier à partir de 2 minutes.

## Réentraîner les réglages

Les réglages de la v4c (spread et marge, choisis par ses voisins) ont été appris avec l'ancienne valeur. Je les ai réappris avec la nouvelle, sur exactement les mêmes 188 tables que le modèle de la v4c, dans le même ordre : les 80 tables du deuxième tour de la v4, les 24 tables pleines de la v4b et les 84 tables symétriques de la v4c. Seule la valeur des réglages joués change. Pour vérifier que je rejouais bien les mêmes tables, j'ai d'abord relancé la première table de chaque sorte sans poids : les trois sont identiques à celles du rapport de la v4c.

En validation croisée (chaque table jugée par un modèle construit sur les autres), le réglage choisi gagne 3,76 $ par manche de plus que le réglage fixe [+3,24 ; +4,27], contre 2,48 $ pour la v4c. Le meilleur réglage possible en gagne 5,05 $ de plus. Sur ces tables, la nouvelle valeur gagne plus avec le réglage fixe (+10,83 $ contre +9,74 $), et le choix du réglage lui apporte un peu plus.

J'ai mis deux candidats au tournoi : `v4c_temps`, avec ses réglages réentraînés, et `v4c_temps_brut`, la même valeur avec les réglages de la v4c. L'écart entre les deux mesure ce qu'apporte le réentraînement.

## Le tournoi

Même format que les phases 5j et 5k : graine 1, 100 donnes de 10 manches, le Hard recalé comme remplissant de la table mixte. J'ai ajouté une douzième référence à la table mixte, la v4c vendeuse de la phase 5k. Comme les donnes sont les mêmes qu'en phase 5k, les chiffres se comparent directement.

Face à trois copies d'un même adversaire (gain du candidat, en dollars par manche) :

| Adversaire | v4c au temps, 4 j. | v4c au temps, 5 j. | sans réentraînement, 4 j. | sans réentraînement, 5 j. | v4c vendeuse, 4 j. (5k) |
|---|---|---|---|---|---|
| heuristique | +42,09 [+39,73 ; +44,46] | +36,78 [+34,96 ; +38,60] | +39,32 | +35,34 | +36,47 |
| sniper | +30,85 [+29,55 ; +32,14] | +27,50 [+26,25 ; +28,75] | +30,85 | +27,50 | +25,86 |
| bayésien | +23,68 [+21,69 ; +25,67] | +22,20 [+20,63 ; +23,77] | +22,61 | +21,22 | +23,08 |
| marginal | +9,74 [+8,81 ; +10,67] | +8,04 [+7,31 ; +8,76] | +10,39 | +7,10 | +7,26 |
| Hard de la phase 5c | +37,40 [+36,00 ; +38,79] | +31,86 [+30,79 ; +32,93] | +36,18 | +33,75 | +36,96 |
| Hard recalé | +15,18 [+13,39 ; +16,97] | +12,78 [+11,49 ; +14,08] | +15,95 | +15,26 | +10,06 |

À la table mixte (écart référence moins candidat, en dollars par manche ; un écart dont tout l'intervalle est au-dessus de 0 refuse le candidat) :

| Référence | v4c au temps, 4 j. | v4c au temps, 5 j. | sans réentraînement, 4 j. | sans réentraînement, 5 j. |
|---|---|---|---|---|
| Hard recalé | -19,96 [-22,48 ; -17,44] | -16,36 [-18,08 ; -14,64] | -21,41 [-23,98 ; -18,85] | -19,15 [-20,98 ; -17,32] |
| bayésien | -24,55 [-26,19 ; -22,92] | -20,14 [-21,54 ; -18,75] | -24,00 [-25,76 ; -22,25] | -19,18 [-20,72 ; -17,64] |
| marginal | -15,13 [-16,87 ; -13,39] | -11,80 [-13,27 ; -10,33] | -10,89 [-12,63 ; -9,14] | -10,79 [-12,15 ; -9,43] |
| v3 | -10,65 [-12,54 ; -8,77] | -8,66 [-10,23 ; -7,09] | -8,05 [-9,87 ; -6,24] | -7,82 [-9,42 ; -6,22] |
| v4b | -7,64 [-9,26 ; -6,02] | -1,79 [-3,22 ; -0,36] | -7,92 [-9,50 ; -6,33] | -4,85 [-6,28 ; -3,43] |
| v4c | -7,27 [-8,84 ; -5,70] | -1,74 [-3,18 ; -0,30] | -7,09 [-8,80 ; -5,38] | -4,80 [-6,22 ; -3,39] |
| v4c calme 60 s | -1,33 [-2,47 ; -0,19] | **+2,46 [+1,51 ; +3,41]** | +1,14 [-0,02 ; +2,29] | **+1,61 [+0,63 ; +2,58]** |
| v4c vendeuse (5k) | -3,49 [-4,63 ; -2,34] | +0,45 [-0,47 ; +1,36] | -2,21 [-3,29 ; -1,14] | -1,91 [-2,75 ; -1,07] |
| exploiteur | -17,50 [-19,07 ; -15,93] | -14,69 [-15,87 ; -13,51] | -20,25 [-21,98 ; -18,52] | -16,95 [-18,34 ; -15,57] |
| exploiteur lecteur | -6,97 [-8,63 ; -5,32] | **+1,66 [+0,23 ; +3,08]** | -5,08 [-6,77 ; -3,40] | **+1,99 [+0,78 ; +3,19]** |
| vendeur | -14,35 [-15,52 ; -13,19] | -9,55 [-10,74 ; -8,36] | -13,17 [-14,41 ; -11,94] | -11,35 [-12,57 ; -10,12] |
| parieur | -13,53 [-15,46 ; -11,60] | -12,82 [-14,15 ; -11,48] | -14,69 [-16,68 ; -12,71] | -13,88 [-15,37 ; -12,38] |

À 4 joueurs, la v4c au temps passe : tous les écarts sont sous 0, et le plus proche, -1,33 $ face à la v4c qui se tait, a tout son intervalle sous 0. C'est la première fois depuis que la table mixte fait partie de la règle d'entrée (phase 5i). À 5 joueurs, deux références la refusent, les mêmes qu'en phase 5k, avec des écarts plus petits.

Face au zoo, elle fait mieux que la v4c vendeuse presque partout, et nettement face au Hard recalé (+15,18 $ contre +10,06 $) et face au marginal (+9,74 $ contre +7,26 $). Le défaut que visait la phase 5k est donc bien corrigé par la valeur elle-même, sans interdire les achats.

Le réentraînement n'apporte rien de net. Les deux versions sont refusées par les mêmes références à 5 joueurs, avec des écarts proches. Face au zoo, la version réentraînée gagne un peu plus face à l'heuristique et au marginal à 5 joueurs, et un peu moins face au Hard recalé. Sa validation croisée promettait +1,3 $ par manche de plus pour le choix du réglage, sur ses tables d'entraînement : ça ne se voit pas au tournoi.

## Ce que lui prennent les deux références à 5 joueurs

J'ai fait jouer chacune des deux références, la v4c au temps et trois Hard recalés, sur 40 parties de 10 manches, dans les deux ordres des sièges. Comme en phase 5k, pour chaque échange je compte ce que le vendeur gagne sur l'acheteur : le prix moins la valeur finale de la carte. Et je compte qui finit avec le plus de cartes objectif. Par manche, les trois Hard ensemble :

| Table | gain de la référence | gain de la v4c au temps | majorité de la référence | majorité de la v4c au temps |
|---|---|---|---|---|
| v4c calme 60 s | -1,08 | -6,13 | 31,8 % | 21,1 % |
| exploiteur lecteur | +1,70 | +0,94 | 40,0 % | 15,5 % |

Face à la v4c qui se tait, les échanges ne jouent presque aucun rôle : entre elles deux, il passe 0,48 $ par manche. Et la v4c qui se tait perd même davantage sur ses échanges avec les Hard (13,86 $ par manche, presque tout en deuxième minute, contre 8,06 $). Elle passe devant par la majorité : 31,8 % des manches contre 21,1 %.

Face à l'exploiteur lecteur, l'argent passe bien par les échanges : il prend 9,00 $ par manche à la v4c au temps pendant la première minute, et presque rien ensuite. Dans cette première minute, il achète 0,61 carte objectif par manche, et la v4c au temps en vend 0,59.

Les deux tables montrent le même défaut : la v4c au temps vend ses cartes objectif. Sur une manche, elle en vend 1,14 et en achète 0,68 à la table de la v4c qui se tait, qui fait l'inverse (0,61 vendues, 0,88 achetées). C'est le coût que je craignais en mettant le poids à la vente : en début de manche, une carte objectif ne vaut plus pour elle que 10 $ fois la chance que sa couleur soit l'objectif, et elle la cède à ce prix à un joueur qui, lui, compte la majorité. La phase 5k s'était arrêtée sur le même constat : on gagne ses échanges, et on perd la majorité.

Ces parties sont simples, sans donnes dupliquées ni intervalle de confiance : elles indiquent où regarder, elles ne mesurent pas l'écart.

## Le bot progresse-t-il ?

Pas au sens de la règle d'entrée : la v4c au temps est refusée à 5 joueurs, et le marginal reste le bot de référence. Mais c'est le candidat qui passe le plus près. Elle passe à 4 joueurs, ce qu'aucun candidat n'avait fait depuis la phase 5i. À 5 joueurs, son pire écart est de +2,46 $ par manche, contre +3,43 $ pour la v4c vendeuse en phase 5k, sur les mêmes donnes. Et elle bat le marginal et le Hard recalé par plus que tous les candidats d'avant.

Ces gains sont mesurés contre des bots simulés : ce ne sont pas des gains réels sur figgie.com.

Comme elle est refusée à 5 joueurs, je n'ai pas lancé le tournoi complet (300 donnes, 19 références) prévu si elle passait aux deux tailles de table.

## Limites

T et k sont choisis sur une grille de neuf points, à 4 joueurs seulement, face à deux sortes de tables. Je n'ai pas cherché de poids différent à 5 joueurs.

Le poids ne dépend que du temps. Il ne tient pas compte de ce que le bot sait déjà de l'objectif, ni du nombre de cartes qui restent à échanger.

Le diagnostic à 5 joueurs porte sur des parties simples, avec des scripts hors dépôt, comme la grille et la vérification des tables d'entraînement.

Le tournoi est réduit comme ceux des phases 5j et 5k : 100 donnes au lieu de 300, et une partie des références. Les intervalles sont environ 1,7 fois plus larges qu'en phase 5i.

Tout reste mesuré contre des bots simulés. Ces gains ne sont pas des gains réels sur figgie.com.

## Reproduire

```bash
cd projets/bot-figgie
python3 -m unittest                                                  # les 138 tests, environ 5 s
python3 -m figgie.adapt --v4t 120,0.5 --deals 40 --rounds 3 \
    --arms 6,3,6,3 8,1,8,1 10,3,10,3 12,3,12,3 8,1,3,1 12,3,4,1 --report entrainement_v4t.json
python3 -m figgie.tournoi --site --candidates v4c_temps v4c_temps_brut --rounds 10 --deals 100 --no-tables \
    --opponents heuristique sniper bayesien marginal hard_simule hard_simule_v2 --references \
    --mixed hard_simule_v2 bayesien marginal adaptatif_v3 adaptatif_v4b adaptatif_v4c v4c_calme_60 v4c_vente_60 \
        exploiteur exploiteur_lecteur vendeur parieur --out tournoi.json
```

Le réentraînement prend environ 4 h sur 10 cœurs et réécrit `modeles/adaptation_v4t.json`. Le tournoi prend environ 4 h 10. Pour revenir exactement au code de cette phase : `git checkout phase5l-figgie`.
