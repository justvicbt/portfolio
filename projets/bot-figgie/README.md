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
| 3. Apprentissage continu | Journaux, mise à jour du modèle, nouvelle version promue seulement si elle bat l'ancienne | | À venir |
| 4. Ligue et robustesse | Auto-jeu, adversaires entraînés à battre le bot, comportements anormaux | | À venir |
| 5. Site réel | Seulement avec l'accord écrit de Jane Street, sinon outil d'entraînement et d'analyse | | À venir |

Le site figgie.com ne publie pas de conditions d'utilisation et ne dit rien des bots. Je n'automatiserai aucune partie classée sans un accord écrit de Jane Street.

## Ce que ça donne

Après la phase 2, le nouveau bot « marginal » gagne contre chaque adversaire du zoo, avec un intervalle de confiance à 95 % entièrement au-dessus de zéro, à 4 comme à 5 joueurs. Son pire adversaire est le joueur passif, que personne ne battait jusque-là : +15,2 $ par manche à 4 joueurs ([+14,0 ; +16,5]). Il bat aussi l'ancien bot de référence, le bayésien, de +20,6 $ par manche. Les tableaux complets sont dans les docs de chaque phase.

## Ce que j'en retiens

Le bayésien ne devine pas mieux la couleur objectif que l'heuristique (38,1 % contre 38,5 %). Il gagne parce qu'il connaît son incertitude et ne brade pas les cartes qui ont une chance sur trois d'être précieuses.

En temps continu, la vitesse change tout : le sniper, qui ne fait que prendre les cotations mal placées, est devenu le deuxième meilleur bot. Et entre bots qui ne changent jamais d'avis, le marché meurt au bout d'une vingtaine de secondes. Apprendre en regardant les autres joueurs sera sans doute le plus gros gain à venir.

Une carte objectif ne vaut pas 10 $ : elle peut faire basculer la majorité et valoir 60 ou 110 $, selon qui la vend et qui l'achète. Le bot qui calcule ça le mieux gagne surtout en attendant les erreurs des autres, avec des cotations prudentes, à 8 $ de sa valeur.

## Limites

Tous les adversaires sont des bots que j'ai écrits. Aucun chiffre de ce projet ne mesure le niveau face à des humains tant que la phase 5 n'a pas eu lieu. Le simulateur repose sur des hypothèses : quatre règles que le site ne précise pas, et des temps de réaction inventés. Les tables ne mélangent pas encore les styles.

## Lancer le projet

Python 3.14, sans aucune dépendance externe.

```bash
cd projets/bot-figgie
python3 -m unittest                      # 50 tests, moins d'une seconde
python3 -m figgie.evaluate --candidate marginal --deals 1000 --seed 1
```

Un candidat contre tout le zoo prend quelques minutes, le tournoi complet de la phase 2 environ 35 minutes sur 10 cœurs. Chaque phase a son étiquette git (`phase0-figgie`, `phase1-figgie`, `phase2-figgie`) pour retrouver le code exact.

## Stack

- Python 3.14, bibliothèque standard uniquement
- unittest pour les tests

## Statut

En cours : phases 0 à 2 terminées. Prochaine étape : apprendre à lire le marché, c'est-à-dire tirer des conclusions des cotations et des échanges des autres joueurs.
