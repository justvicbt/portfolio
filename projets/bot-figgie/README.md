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
| 1. Simulateur fidèle | Règles de figgie.com, temps continu, latence, 4 et 5 joueurs | | À venir |
| 2. Professeur bayésien | Valeur marginale d'une carte par Monte Carlo, comptage des cartes, exécution | | À venir |
| 3. Apprentissage continu | Journaux, mise à jour du modèle, nouvelle version promue seulement si elle bat l'ancienne | | À venir |
| 4. Ligue et robustesse | Auto-jeu, adversaires entraînés à battre le bot, comportements anormaux | | À venir |
| 5. Site réel | Seulement avec l'accord écrit de Jane Street, sinon outil d'entraînement et d'analyse | | À venir |

Le site figgie.com ne publie pas de conditions d'utilisation et ne dit rien des bots. Je n'automatiserai aucune partie classée sans un accord écrit de Jane Street.

## Ce que ça donne

Après la phase 0, le bot bayésien est le plus fort des cinq. Contre l'heuristique, il gagne +41,4 $ par manche à 4 joueurs (intervalle à 95 % : [+38,4 ; +44,3]) et +43,1 $ à 5 joueurs. Contre un joueur passif, qui cote large et ne prend jamais rien, il ne gagne rien du tout : +0,02 $, faute d'échanges. Le détail et les tableaux complets sont dans la [doc de la phase 0](docs/phase0.fr.md).

## Ce que j'en retiens

Le bayésien ne devine pas mieux la couleur objectif que l'heuristique (38,1 % contre 38,5 %). Il gagne parce qu'il connaît son incertitude et ne brade pas les cartes qui ont une chance sur trois d'être précieuses.

## Limites

Tous les adversaires sont des bots que j'ai écrits. Aucun chiffre de ce projet ne mesure le niveau face à des humains tant que la phase 5 n'a pas eu lieu. Le simulateur est encore simplifié (temps découpé en ticks, tables sans mélange de styles).

## Lancer le projet

Python 3.14, sans aucune dépendance externe.

```bash
cd projets/bot-figgie
python3 -m unittest                      # 27 tests, moins d'une seconde
python3 -m figgie.evaluate --candidate bayesien --deals 1000 --seed 1
```

Un tournoi d'un candidat contre tout le zoo prend une vingtaine de secondes, les 10 configurations de la phase 0 environ 4 minutes.

## Stack

- Python 3.14, bibliothèque standard uniquement
- unittest pour les tests

## Statut

En cours : phase 0 terminée. Prochaine étape : un simulateur plus fidèle à figgie.com.
