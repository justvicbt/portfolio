# Phase 0 : des fondations pour mesurer

*English version: [phase0.en.md](phase0.en.md)*

Avant d'écrire un bot qui apprend, il me fallait de quoi savoir s'il progresse vraiment. Cette phase construit trois choses : un moteur de jeu testé, une famille d'adversaires et une méthode d'évaluation qui sépare le talent de la chance. Elle se termine par un premier tournoi qui sert de point de départ pour tout le reste du projet.

## Le jeu en deux minutes

Figgie a été inventé chez Jane Street en 2013 pour entraîner les traders. On joue à 4 ou 5. Chaque joueur reçoit 350 $ et en verse une partie au pot, qui contient toujours 200 $ (50 $ chacun à 4 joueurs, 40 $ à 5).

Le paquet a 40 cartes réparties en quatre couleurs, mais pas de façon égale : une couleur a 12 cartes, deux en ont 10 et la dernière 8. Personne ne sait laquelle est laquelle. La couleur qui compte, appelée couleur objectif, est la jumelle de la couleur de 12 cartes, c'est-à-dire l'autre couleur de même teinte. Si les piques sont la couleur de 12, l'objectif est le trèfle. L'objectif a donc forcément 8 ou 10 cartes.

Pendant 4 minutes, tout le monde achète et vend des cartes, sans tour de parole. À la fin, chaque carte objectif rapporte 10 $, et ce qui reste du pot va au joueur qui en a le plus. Avec 10 cartes objectif, il reste 100 $ pour la majorité, avec 8 il en reste 120 $. En cas d'égalité, on partage.

Deux règles de marché comptent beaucoup. Un échange porte sur une seule carte. Et après chaque échange, toutes les cotations de tous les joueurs sont effacées. On ne peut donc pas laisser traîner une offre : chaque information nouvelle remet le marché à zéro.

## Le moteur

Le moteur tient dans un fichier, [`figgie/engine.py`](../figgie/engine.py). Il distribue les cartes, tient le carnet d'ordres, exécute les échanges et calcule le score.

Le carnet garde, pour chaque couleur, la meilleure offre d'achat (le prix le plus haut qu'un joueur accepte de payer) et la meilleure offre de vente (le prix le plus bas qu'un joueur accepte de recevoir). Une nouvelle offre doit battre la précédente. Si quelqu'un propose d'acheter au prix d'une vente affichée, ou plus cher, l'échange se fait au prix affiché, comme sur une vraie bourse. Le moteur refuse tout ce qui est impossible : vendre une carte qu'on n'a pas, offrir plus d'argent qu'on n'en possède, traiter avec soi-même, envoyer une action mal formée.

Le temps est simplifié pour l'instant. La manche est découpée en 200 « ticks ». À chaque tick, chaque joueur agit une fois, dans un ordre tiré au sort. La phase 1 remplacera ce découpage par un temps continu, plus proche du vrai site.

Un bot ne voit que ce qu'un joueur humain verrait : sa main, son argent, le carnet, l'historique public des échanges et le nombre de cartes de chacun. Les mains des autres restent cachées.

Chaque manche produit un journal en JSON : la donne, chaque action dans l'ordre et si elle a été acceptée. Rejouer ce journal sans les bots redonne exactement le même résultat. C'est la base de la suite du projet, parce que ces journaux deviendront les données d'entraînement du bot qui apprend. Si un journal a été modifié, le rejeu le détecte et s'arrête au lieu de produire des chiffres faux.

## Les tests

J'ai écrit le moteur en TDD : d'abord un test qui échoue, puis le code minimal pour le faire passer. Les 27 tests se lancent en moins d'une seconde et couvrent quatre points d'entrée.

La manche complète. Le paquet a bien 12, 10, 10 et 8 cartes, l'objectif est la jumelle de la couleur de 12, chaque joueur a 10 cartes à 4 et 8 à 5. Le score est vérifié sur des exemples calculés à la main, égalités comprises. Sur des dizaines de manches, l'argent total ne change pas : ce que l'un gagne, un autre l'a perdu.

Le carnet d'ordres. Un échange déplace exactement une carte et le prix convenu. Après un échange, toutes les cotations disparaissent, y compris dans les autres couleurs. Les actions impossibles sont refusées.

Le journal. Il passe en JSON et revient sans perte, son rejeu redonne les mêmes gains, et une falsification est détectée.

L'évaluation, décrite plus bas. Un des tests vérifie qu'un bot face à des copies de lui-même gagne exactement zéro sur chaque donne. Si la rotation des sièges oubliait un siège, ce test échouerait.

## Les adversaires

Un bot qui bat un seul type d'adversaire peut très bien perdre contre un autre. Le zoo en compte donc cinq, dans [`figgie/bots.py`](../figgie/bots.py).

| Bot | Comment il joue |
|---|---|
| aléatoire | Agit une fois sur trois, au hasard : une cotation entre 1 et 20 $, ou il prend celle d'un autre. |
| heuristique | Suppose que sa couleur la plus longue est celle de 12 cartes. Il estime la jumelle à 12 $ et le reste à 0 $. |
| bayésien | Calcule la probabilité que chaque couleur soit l'objectif, puis estime une carte à probabilité × (10 $ + 5 $ de bonus). |
| agressif | Même croyance que l'heuristique, mais il paie jusqu'à 20 $, cote serré et agit à chaque tick. |
| passif | Mêmes estimations que le bayésien, mais il cote large, rarement, et ne prend jamais une cotation. |

Les quatre derniers partagent la même mécanique. Ils estiment ce que vaut une carte de chaque couleur. S'ils voient une vente affichée sous cette valeur, ils achètent. S'ils voient un achat affiché au-dessus, ils vendent. Sinon, ils proposent un prix d'achat un peu en dessous de leur valeur et un prix de vente un peu au-dessus.

Le calcul du bayésien mérite une explication, parce que tout le projet va s'appuyer dessus. Il n'existe que 12 compositions de paquet possibles : 4 choix pour la couleur de 12 cartes, puis 3 pour celle de 8. Pour chacune, on peut compter de combien de façons on aurait pu recevoir exactement sa main (c'est la loi hypergéométrique, celle des tirages sans remise). Plus ce nombre est grand, plus la composition est plausible. En additionnant par couleur objectif, on obtient une probabilité. Avec 6 piques en main, par exemple, le trèfle a 61 % de chances d'être l'objectif.

J'ai vérifié que ces probabilités sont honnêtes sur 20 000 donnes. Quand le bot annonce 30 %, la couleur est l'objectif 28 % du temps. Quand il annonce 50 %, 48 % du temps. Avec sa seule main, la couleur qu'il juge la plus probable est la bonne dans 38 % des cas, contre 25 % au hasard.

## Comment on mesure : les donnes dupliquées

Au Figgie, la donne pèse énormément. Un joueur qui reçoit 5 cartes objectif gagne presque à coup sûr, même s'il joue mal. Comparer deux bots sur des donnes différentes revient donc surtout à mesurer leur chance.

Les donnes dupliquées règlent ce problème, comme au bridge en tournoi. On fixe une donne, et on la rejoue autant de fois qu'il y a de sièges. Le bot testé passe par chaque siège, donc il reçoit tour à tour chacune des mains, la bonne comme les mauvaises. On fait la moyenne de ses gains sur ces rotations. La chance de la donne s'annule, et il reste la différence de jeu. Tous les adversaires affrontent en plus les mêmes donnes, ce qui rend les comparaisons entre eux plus justes.

Pour chaque adversaire, le tournoi joue 1 000 donnes, soit 4 000 manches à 4 joueurs et 5 000 à 5. J'en tire le gain moyen par manche et un intervalle de confiance à 95 %. Si on rejouait l'expérience un grand nombre de fois, l'intervalle contiendrait le vrai gain moyen 95 fois sur 100. Quand il est entièrement au-dessus de zéro, on peut dire que le bot gagne vraiment. Quand il contient zéro, on ne peut rien affirmer.

Le projet s'impose une règle d'entrée. Un nouveau bot n'est accepté que si son intervalle contre l'heuristique est entièrement au-dessus de zéro. L'objectif à long terme est plus exigeant : un gain positif contre chaque adversaire du zoo, y compris le pire.

## Résultats

Gain moyen en dollars par manche du bot en ligne, face à des copies du bot en colonne (3 copies à 4 joueurs, 4 à 5). Les intervalles de confiance sont dans le dossier [`resultats/phase0/`](../resultats/phase0/). Ils font tous moins de ±4 $ de demi-largeur.

### À 4 joueurs

| Candidat \ adversaires | aléatoire | heuristique | bayésien | agressif | passif |
|---|---|---|---|---|---|
| aléatoire | | -43,2 | -92,0 | +35,7 | -32,2 |
| heuristique | +40,0 | | -27,1 | +57,6 | -5,2 |
| bayésien | +120,7 | +41,4 | | +107,9 | +0,0 |
| agressif | -35,6 | -54,2 | -95,1 | | -0,2 |
| passif | +29,5 | +4,2 | -6,1 | -13,2 | |

### À 5 joueurs

| Candidat \ adversaires | aléatoire | heuristique | bayésien | agressif | passif |
|---|---|---|---|---|---|
| aléatoire | | -54,2 | -90,1 | +21,5 | -26,5 |
| heuristique | +47,4 | | -25,5 | +58,7 | +2,4 |
| bayésien | +126,3 | +43,1 | | +104,1 | -0,0 |
| agressif | -29,7 | -58,3 | -95,5 | | +1,1 |
| passif | +27,6 | -1,9 | -6,5 | -11,5 | |

Le bayésien est le plus fort du zoo. Il passe la règle d'entrée à 4 comme à 5 joueurs : +41,4 $ par manche contre l'heuristique à 4 joueurs, intervalle [+38,4 ; +44,3]. C'est le bot de référence que les phases suivantes devront battre.

Il ne remplit pas pour autant l'objectif final. Contre le passif, il gagne +0,02 $ par manche, avec un intervalle [-0,12 ; +0,17] qui contient zéro. En pratique, il ne se passe presque rien : à peine 0,2 échange par manche entre eux. Le passif cote trop large pour que le bayésien vienne le chercher, et lui ne prend jamais rien. Sans échange, les donnes dupliquées ramènent tout le monde à zéro. Pour gagner contre un joueur prudent, il faudra savoir reconnaître quand ses cotations sont mal placées et les prendre. C'est le travail des phases 2 et 4.

## Ce que j'en retiens

Le bayésien ne gagne pas parce qu'il devine mieux. J'ai mesuré les deux sur 20 000 donnes : l'heuristique trouve la bonne couleur objectif dans 38,5 % des cas, le bayésien dans 38,1 %. La différence vient du prix. L'heuristique est sûre d'elle, alors elle vend à 2 $ toutes les cartes qu'elle juge inutiles, y compris celles qui ont 30 % de chances d'être l'objectif. Le bayésien, lui, connaît son incertitude et ne brade pas ces cartes.

Les adversaires ne se classent pas sur une seule échelle. L'agressif perd contre l'aléatoire (-35,6 $ à 4 joueurs), sans doute parce qu'il paie 20 $ des cartes que l'aléatoire lui vend au hasard, et qui sont souvent les mauvaises. Le passif bat l'heuristique à 4 joueurs (+4,2 $) mais perd contre elle à 5 (-1,9 $). D'où l'intérêt de tester contre tout le zoo, à 4 et à 5 joueurs.

Un script de mesure a failli me tromper. Mon premier script de comparaison donnait 45 % de réussite à l'heuristique. J'avais créé le générateur aléatoire de son tirage au sort avec la même graine que la donne. Son premier tirage reproduisait donc celui qui fixe la couleur de 12 cartes, et l'heuristique trichait sans le savoir. Le moteur n'a pas ce défaut : chaque bot a son propre générateur, initialisé avec une graine différente de celle de la donne. Mais cela montre qu'un chiffre trop beau mérite toujours une vérification.

## Limites

Tous ces adversaires sont des bots que j'ai écrits moi-même. Un gain contre eux ne dit rien du niveau contre des humains sur figgie.com. Ces chiffres ne mesurent que la force relative des bots entre eux.

L'heuristique de ce projet est une réécriture, plus simple que celle de mon ancien code. Dans l'ancienne version, le bayésien perdait contre l'heuristique. Ici il gagne largement, en partie parce que cette heuristique-là brade ses cartes. Les deux résultats ne sont pas comparables, et la barre d'entrée est sans doute trop basse. Il faudra ajouter des adversaires plus durs.

Le temps découpé en ticks est irréaliste. Sur le vrai site, la vitesse compte : le premier à prendre une cotation mal placée l'emporte. La phase 1 s'en occupe.

Les tables ne mélangent pas les styles. Chaque match oppose le candidat à des copies d'un seul adversaire. Une vraie table de figgie.com mélange des joueurs différents.

En cas d'égalité, le partage du pot n'est pas arrondi (33,33 $ chacun pour 100 $ partagés en trois). Je ne sais pas encore comment figgie.com arrondit.

## Reproduire

Le code a évolué depuis. Pour retrouver exactement celui de la phase 0, il faut d'abord revenir à son étiquette git : `git checkout phase0-figgie`.

```bash
cd projets/bot-figgie
python3 -m unittest                      # les 27 tests, moins d'une seconde
python3 -m figgie.evaluate --candidate bayesien --deals 1000 --seed 1
```

Un tournoi d'un candidat contre le zoo prend une vingtaine de secondes. Les 10 configurations du tableau (5 candidats, à 4 et à 5 joueurs) prennent environ 4 minutes sur un MacBook. Ajouter `--logs parties.jsonl` enregistre le journal de chaque manche.

## Et ensuite

La phase 1 rendra le simulateur plus fidèle à figgie.com : une cotation par joueur et par couleur, des limites d'argent, un temps continu avec de la latence. Le tournoi sera rejoué dans ces conditions pour voir si le classement tient.
