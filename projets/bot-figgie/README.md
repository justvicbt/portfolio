# Bot Figgie

*Un bot pour Figgie, le jeu de cartes de marché inventé chez Jane Street, construit pas à pas : d'abord un simulateur et une méthode de mesure, puis un bot qui apprend de chaque partie.*

*English version: [README.en.md](README.en.md)*

## Pourquoi ce projet

Figgie ressemble à une salle de marché en miniature. Personne ne connaît la valeur des cartes, tout le monde achète et vend en même temps, et les prix des autres trahissent ce qu'ils savent. Je voulais voir jusqu'où un programme peut apprendre à y jouer : estimer une valeur dans l'incertitude, éviter de vendre à quelqu'un qui en sait plus que lui, et progresser partie après partie.

Le but final est un bot dont le gain moyen par manche reste positif contre tous les types d'adversaires, avec un intervalle de confiance qui exclut zéro, et qui continue de s'améliorer à mesure qu'il joue. Gagner chaque manche est impossible : la donne est aléatoire et une partie de l'information reste cachée. Ce qui peut progresser sans fin, c'est le gain moyen et le classement.

## Ce que j'ai fait

Le projet avance par phases. Chacune a sa propre doc, en français et en anglais, et se termine par un tournoi chiffré comparé à la phase précédente.

| Phase | Contenu | Doc | Statut |
|---|---|---|---|
| 0. Fondations | Moteur testé, zoo de 5 adversaires, évaluation par donnes dupliquées, journal de chaque partie | [FR](docs/phase0.fr.md) · [EN](docs/phase0.en.md) | Terminée |
| 1. Simulateur fidèle | Une cotation par joueur, temps continu, latence, prises au prix vu, nouvel adversaire « sniper » | [FR](docs/phase1.fr.md) · [EN](docs/phase1.en.md) | Terminée |
| 2. Valeur marginale | Valeur d'une carte par Monte Carlo selon le joueur d'en face, comptage des cartes, réglage sur des donnes séparées | [FR](docs/phase2.fr.md) · [EN](docs/phase2.en.md) | Terminée |
| 3. Lire le marché | Modèle de signaux appris sur des parties simulées, comptage corrigé, parties de plusieurs manches avec mémoire des adversaires | [FR](docs/phase3.fr.md) · [EN](docs/phase3.en.md) | Terminée (bot non promu) |
| 4. Ligue et robustesse | Moteur accéléré, test de minorité, exploiteurs trouvés par recherche, ligue, joueur inactif, spammeur et menteurs | [FR](docs/phase4.fr.md) · [EN](docs/phase4.en.md) | Terminée (aucun bot promu) |
| 5. Adaptation en cours de partie | Reconnaître la table par plus proches voisins et choisir son spread et sa marge manche après manche, tournoi en parties de 10 manches | [FR](docs/phase5.fr.md) · [EN](docs/phase5.en.md) | Terminée (aucun bot promu) |
| 6. Site réel | Seulement avec l'accord écrit de Jane Street, sinon outil d'entraînement et d'analyse | | À venir |

Le site figgie.com ne publie pas de conditions d'utilisation et ne dit rien des bots. Je n'automatiserai aucune partie classée sans un accord écrit de Jane Street.

## Ce que ça donne

Après la phase 2, le nouveau bot « marginal » gagne contre chaque adversaire du zoo, avec un intervalle de confiance à 95 % entièrement au-dessus de zéro, à 4 comme à 5 joueurs. Son pire adversaire est le joueur passif, que personne ne battait jusque-là : +15,2 $ par manche à 4 joueurs ([+14,0 ; +16,5]). Il bat aussi l'ancien bot de référence, le bayésien, de +20,6 $ par manche.

En phase 3, le bot « lecteur », qui lit aussi les cotations des autres, devine beaucoup mieux la couleur objectif (52 % à une minute, contre 42 %). Mais il ne gagne qu'un peu plus que le marginal à 4 joueurs (+2,7 $ par manche) et ne le bat pas nettement à 5. Il n'est donc pas promu : le marginal reste le bot de référence.

En phase 4, une recherche automatique a trouvé des adversaires qui battent le marginal quand il est en minorité (+4,35 $ par manche seul face à trois marginaux, +7,22 $ face à quatre). Aucun candidat ne passe la règle d'entrée complète, test de minorité compris. Avec des réglages fixes, chaque bot a sa contre-stratégie.

En phase 5, le bot « adaptatif » choisit son spread et sa marge selon la table qu'il reconnaît. Il bat le marginal en tête-à-tête (+2,00 $ par manche à 4 joueurs, +3,47 $ à 5), et l'exploiteur de la phase 4 ne lui prend plus que 1,54 $ par manche au lieu de 4,32 $. Mais un sniper seul face à ses copies gagne +3,72 $ par manche : il ne passe pas le test de minorité et n'est pas promu. Les tableaux complets sont dans les docs de chaque phase.

## Ce que j'en retiens

Le bayésien ne devine pas mieux la couleur objectif que l'heuristique (38,1 % contre 38,5 %). Il gagne parce qu'il connaît son incertitude et ne brade pas les cartes qui ont une chance sur trois d'être précieuses.

En temps continu, la vitesse change tout : le sniper, qui ne fait que prendre les cotations mal placées, est devenu le deuxième meilleur bot. Et entre bots qui ne changent jamais d'avis, le marché meurt au bout d'une vingtaine de secondes. Apprendre en regardant les autres joueurs sera sans doute le plus gros gain à venir.

Une carte objectif ne vaut pas 10 $ : elle peut faire basculer la majorité et valoir 60 ou 110 $, selon qui la vend et qui l'achète. Le bot qui calcule ça le mieux gagne surtout en attendant les erreurs des autres, avec des cotations prudentes, à 8 $ de sa valeur.

Mieux deviner ne suffit pas à mieux gagner : l'information arrive quand le marché est déjà presque mort. Et mesurer la calibration (« quand le bot annonce 80 %, a-t-il raison 80 % du temps ? ») a révélé un défaut de raisonnement présent depuis la phase 2.

Un bot à réglages fixes est une cible : quand il est nombreux à la table, ses copies se font concurrence et un joueur différent en profite. D'où la phase 5, un bot qui adapte son jeu en cours de partie.

Un bandit qui apprend sur ses gains ne voit que du bruit : le gain d'une manche varie d'environ 65 $ d'une donne à l'autre. Reconnaître la façon de jouer des autres marche mieux. Mais quand toutes les copies du bot reconnaissent la même table, elles changent de réglage ensemble et retombent dans la même guerre des prix.

## Limites

Tous les adversaires sont des bots que j'ai écrits. Aucun chiffre de ce projet ne mesure le niveau face à des humains tant que la phase 6 (site réel) n'a pas eu lieu. Le simulateur repose sur des hypothèses : quatre règles que le site ne précise pas, et des temps de réaction inventés. Les tables ne mélangent pas encore les styles.

## Lancer le projet

Python 3.14, sans aucune dépendance externe.

```bash
cd projets/bot-figgie
python3 -m unittest                      # 97 tests, environ 5 secondes
python3 -m figgie.evaluate --candidate marginal --deals 1000 --seed 1
```

Un candidat contre tout le zoo prend quelques minutes, le tournoi de la phase 4 (`python3 -m figgie.tournoi`) environ 1 h 15 sur 10 cœurs. Chaque phase a son étiquette git (`phase0-figgie` à `phase5-figgie`) pour retrouver le code exact.

## Stack

- Python 3.14, bibliothèque standard uniquement
- unittest pour les tests

## Statut

En cours : phases 0 à 5 terminées. Prochaine étape : entraîner le bot adaptatif sur des tables qui contiennent ses propres copies. La phase 6 (site réel) attend un accord écrit de Jane Street.
