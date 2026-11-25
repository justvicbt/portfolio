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
| 5b. Jouer contre ses copies | Comptage avec les ventes proposées, spread qui se resserre avec le temps, entraînement contre ses propres copies, force de la main | [FR](docs/phase5b.fr.md) · [EN](docs/phase5b.en.md) | Terminée (aucun bot promu) |
| 5c. Un marché plus proche du site | Règle du site pour les cotations, bot Hard simulé réglé sur 60 vraies manches, rejeu des vraies manches sur le papier, tournoi sur ce marché | [FR](docs/phase5c.fr.md) · [EN](docs/phase5c.en.md) | Terminée (aucun bot promu) |
| 5d. Lire le marché du site | Lecture du marché par fenêtres d'une minute, avec le consensus et la confiance par joueur, puis une v4 entraînée sur le marché du site | [FR](docs/phase5d.fr.md) · [EN](docs/phase5d.en.md) | Terminée (aucun bot promu) |
| 5e. Deux questions de la 5d | Majorité estimée dans le rejeu des vraies manches, puis une v4b entraînée aussi sur des tables où personne ne cote | [FR](docs/phase5e.fr.md) · [EN](docs/phase5e.en.md) | Terminée (aucun bot promu) |
| 5f. Le test de minorité | Pourquoi l'exploiteur gagne face aux copies, puis une v4c entraînée sur des tables où chaque réglage est jugé au gain moyen des copies | [FR](docs/phase5f.fr.md) · [EN](docs/phase5f.en.md) | Terminée (aucun bot promu) |
| 5g. Des copies qui jouent ensemble | Faire jouer toutes les copies au même réglage, six nouvelles références tirées d'un article et de quatre dépôts, se taire la première minute, et un contrôle des intervalles par bootstrap | [FR](docs/phase5g.fr.md) · [EN](docs/phase5g.en.md) | Terminée (aucun bot promu) |
| 5h. Décrire la table sur plusieurs manches | Une v4d qui fait la moyenne des profils des manches passées avant de consulter ses voisins, et des références qui battent l'offre affichée | [FR](docs/phase5h.fr.md) · [EN](docs/phase5h.en.md) | Terminée (aucun bot promu) |
| 5i. Ce que mesure le test de minorité | D'où vient le gain de l'exploiteur face aux copies, puis une table mixte avec des Hard simulés qui remplace le test de minorité dans la règle d'entrée | [FR](docs/phase5i.fr.md) · [EN](docs/phase5i.en.md) | Terminée (aucun bot promu) |
| 5j. Un Hard simulé qui ne paie plus trop cher | Comment finissent les offres de vente sur les vraies manches, un Hard simulé recalé sur la part des offres prises, et la règle d'entrée rejouée avec lui | [FR](docs/phase5j.fr.md) · [EN](docs/phase5j.en.md) | Terminée (aucun bot promu) |
| 5k. Ne rien acheter la première minute | Ce que la v4c achète en première minute et pourquoi elle le surpaie, puis une v4c qui vend mais n'achète rien pendant 60 s | [FR](docs/phase5k.fr.md) · [EN](docs/phase5k.en.md) | Terminée (aucun bot promu) |
| 5l. Une valeur qui tient compte du temps | La part de majorité comptée moins fort en début de manche, avec un poids qui monte jusqu'à 2 minutes, et les réglages réentraînés | [FR](docs/phase5l.fr.md) · [EN](docs/phase5l.en.md) | Terminée (aucun bot promu) |
| 5m. Trois défauts corrigés | Retrait d'un seul côté, valeur d'achat du marginal, profil de table qui suit la règle du site, et la v4c réentraînée | [FR](docs/phase5m.fr.md) · [EN](docs/phase5m.en.md) | Terminée (aucun bot promu) |
| 6. Site réel | Seulement avec l'accord écrit de Jane Street, sinon outil d'entraînement et d'analyse | | À venir |

Le site figgie.com ne publie pas de conditions d'utilisation et ne dit rien des bots. Je n'automatiserai aucune partie classée sans un accord écrit de Jane Street.

## Ce que ça donne

Après la phase 2, le nouveau bot « marginal » gagne contre chaque adversaire du zoo, avec un intervalle de confiance à 95 % entièrement au-dessus de zéro, à 4 comme à 5 joueurs. Son pire adversaire est le joueur passif, que personne ne battait jusque-là : +15,2 $ par manche à 4 joueurs ([+14,0 ; +16,5]). Il bat aussi l'ancien bot de référence, le bayésien, de +20,6 $ par manche.

En phase 3, le bot « lecteur », qui lit aussi les cotations des autres, devine beaucoup mieux la couleur objectif (52 % à une minute, contre 42 %). Mais il ne gagne qu'un peu plus que le marginal à 4 joueurs (+2,7 $ par manche) et ne le bat pas nettement à 5. Il n'est donc pas promu : le marginal reste le bot de référence.

En phase 4, une recherche automatique a trouvé des adversaires qui battent le marginal quand il est en minorité (+4,35 $ par manche seul face à trois marginaux, +7,22 $ face à quatre). Aucun candidat ne passe la règle d'entrée complète, test de minorité compris. Avec des réglages fixes, chaque bot a sa contre-stratégie.

En phase 5, le bot « adaptatif » choisit son spread et sa marge selon la table qu'il reconnaît. Il bat le marginal en tête-à-tête (+2,00 $ par manche à 4 joueurs, +3,47 $ à 5), et l'exploiteur de la phase 4 ne lui prend plus que 1,54 $ par manche au lieu de 4,32 $. Mais un sniper seul face à ses copies gagne +3,72 $ par manche : il ne passe pas le test de minorité et n'est pas promu.

En phase 5b, la v3 du bot adaptatif s'entraîne contre ses propres copies. Elle bat le marginal de +8,48 $ par manche à 4 joueurs, et le sniper comme le preneur de la phase 5 perdent de nouveau face à ses copies. Mais un « coteur serré » trouvé par la recherche automatique lui prend +6,25 $ par manche, et l'exploiteur de la phase 4 +7,79 $ à 5 joueurs. Chaque candidat a son exploiteur, comme à pierre-feuille-ciseaux. Aucun bot n'est promu.

En phase 5c, le simulateur se rapproche du site grâce aux journaux de vraies parties de Rasmus Suonio : la règle du site pour les cotations, et un bot Hard simulé dont le marché ressemble à celui de figgie.com. À une table de Hard simulés, la v3 gagne +22,37 $ par manche à 4 joueurs, contre +20,03 $ pour la v2 et +16,58 $ pour le marginal. Mais elle reste exploitée par l'exploiteur de la phase 4 et par le bayésien, et aucun bot n'est promu. Rejoués sur le papier à la place du bot de Rasmus, face aux vrais bots du site, seul le bayésien gagne (+8,97 $ par manche), et la v3 perd 18,83 $.

En phase 5d, la lecture du marché apprend que, sur le site, une offre d'achat ne veut pas dire la même chose à la première minute et à la dernière. Elle ne fait plus pire que la donne seule en début de manche. La v4, entraînée sur le marché du site avec cette lecture, gagne +35,81 $ par manche à une table de Hard simulés, contre +22,37 $ pour la v3, et fait 14 $ de mieux que la v3 par manche sur les vraies manches rejouées sur le papier. Le bayésien ne l'exploite plus, mais l'exploiteur de la phase 4 gagne toujours face à ses copies, et la v3 aussi. Aucun bot n'est promu.

En phase 5e, le rejeu des vraies manches compte enfin la majorité, estimée à partir de mains des bots du site compatibles avec le journal. Le classement s'inverse : le bayésien, qui vend ses cartes objectif à 10 $, passe de la deuxième place à la dernière, et la v4 passe en tête. La v4b, entraînée aussi sur des tables où personne ne cote, gagne +27,32 $ par manche face au sniper, contre +13,11 $ pour la v4, et fait jeu égal avec elle ailleurs. Elle échoue toujours au test de minorité, face aux mêmes trois joueurs. Aucun bot n'est promu.

En phase 5f, je trouve pourquoi l'exploiteur gagne face aux copies de mes bots : une copie qui lui achète ses cartes y gagne, mais l'ensemble des copies y perd, et mon entraînement ne jugeait qu'au gain d'une seule copie. La v4c, entraînée en jugeant chaque réglage au gain moyen des copies, laisse à l'exploiteur 3,15 $ par manche à 4 joueurs et 4,65 $ à 5, contre 4,05 et 5,85 $ pour la v4b. Mais elle échoue toujours au test de minorité, face aux mêmes trois joueurs, et aucun bot n'est promu.

En phase 5g, je fais jouer toutes les copies au même réglage. Ça ne réduit pas ce que l'exploiteur leur prend : quand elles s'accordent, c'est sur le mauvais réglage. Je n'écris donc pas de v4d. J'ajoute aussi six références tirées d'un article et de quatre dépôts sur Figgie : aucune ne gagne d'argent face aux copies de la v4c. Me taire la première minute, une idée de l'article, coûte environ 8 $ par manche contre le marginal sans rien retirer à l'exploiteur. Un bootstrap confirme mes intervalles de confiance à 1,8 % près. Décrire la table par la moyenne de plusieurs manches retire 0,6 à 0,8 $ par manche à l'exploiteur : c'est la piste pour la suite.

En phase 5h, j'en fais une v4d. Au tournoi, l'exploiteur lui prend un peu moins qu'à la v4c (+2,77 $ par manche à 4 joueurs contre +3,15 $), mais elle échoue toujours au test de minorité et gagne un peu moins contre le marginal : elle n'est pas promue.

En phase 5i, je trouve ce que mesure le test de minorité : les copies ne paient pas trop cher les cartes de l'exploiteur, elles perdent la majorité qu'elles se prennent entre elles. Je le remplace par une table mixte, la référence et le candidat avec des Hard simulés. La v4c y est refusée plus nettement encore : l'exploiteur fait environ 10 $ de mieux qu'elle par manche, surtout en vendant aux Hard des cartes hors objectif.

En phase 5j, je vérifie ce point sur les vraies manches : les bots du site ne prennent presque jamais une offre de vente hors objectif à 7 $ ou plus (1 % des cas), mes Hard simulés en prenaient 9 à 36 %. Je recale le Hard simulé sur cette mesure. Face à lui, l'exploiteur perd 12 $ par manche, et la v4c qui se tait la première minute en gagne 12,56. Au tournoi, la v4c est refusée par le Hard recalé lui-même, et la v4c qui se tait ne bat plus le marginal face à ses copies : aucun bot n'est promu.

En phase 5k, je trouve pourquoi la v4c surpaie en première minute : elle ne sait pas encore quelle couleur est l'objectif, et sa valeur compte la majorité comme si plus rien ne s'échangeait. Une v4c qui vend mais n'achète rien pendant 60 s bat à la fois le marginal (+7,26 $ par manche à 4 joueurs) et le Hard recalé (+10,06 $). Elle est refusée : à la table mixte, la v4c qui se tait fait 1,57 à 1,81 $ de mieux qu'elle, et l'exploiteur lecteur 3,43 $ à 5 joueurs. Elle gagne ses échanges, mais laisse la majorité aux autres. Aucun bot n'est promu.

En phase 5l, je corrige la valeur elle-même : la part de majorité compte avec un poids min(1, t / 120) ^ 0,5, nul au début de la manche et entier à 2 minutes. La nouvelle v4c bat le marginal (+9,74 $ par manche à 4 joueurs) et le Hard recalé (+15,18 $) mieux que tous les candidats d'avant, et c'est la première à passer la règle d'entrée à 4 joueurs. Elle est refusée à 5 : la v4c qui se tait fait 2,46 $ de mieux qu'elle à la table mixte, et l'exploiteur lecteur 1,66 $. Elle vend trop tôt ses cartes objectif, parce que le poids compte aussi à la vente. Réentraîner ses réglages n'apporte rien de net. Aucun bot n'est promu.

En phase 5m, je corrige trois erreurs trouvées à la relecture : sous la règle du site, le bot retirait ses deux offres quand il voulait n'en baisser qu'une ; la valeur d'achat du marginal oubliait qu'un vendeur prouve qu'il a la carte quand la couleur n'est pas l'objectif ; et le profil de table gardait des offres que le site avait effacées. J'ai réentraîné la v4c et la v4c au temps sur le code corrigé. Au tournoi, la v4c au temps passe toujours à 4 joueurs et reste refusée à 5, par une seule référence au lieu de deux : la v4c qui se tait, qui fait 3,05 $ de mieux qu'elle. Presque tous les bots ont changé avec ces corrections, donc les chiffres ne se comparent pas directement à ceux de la 5l. Aucun bot n'est promu.

Les tableaux complets sont dans les docs de chaque phase.

## Ce que j'en retiens

Le bayésien ne devine pas mieux la couleur objectif que l'heuristique (38,1 % contre 38,5 %). Il gagne parce qu'il connaît son incertitude et ne brade pas les cartes qui ont une chance sur trois d'être précieuses.

En temps continu, la vitesse pèse lourd : le sniper, qui ne fait que prendre les cotations mal placées, est devenu le deuxième meilleur bot. Et entre bots qui ne changent jamais d'avis, le marché meurt au bout d'une vingtaine de secondes. Apprendre en regardant les autres joueurs sera sans doute le plus gros gain à venir.

Une carte objectif ne vaut pas 10 $ : elle peut faire basculer la majorité et valoir 60 ou 110 $, selon qui la vend et qui l'achète. Le bot qui calcule ça le mieux gagne surtout en attendant les erreurs des autres, avec des cotations prudentes, à 8 $ de sa valeur.

Mieux deviner ne suffit pas à mieux gagner : l'information arrive quand le marché est déjà presque mort. Et mesurer la calibration (« quand le bot annonce 80 %, a-t-il raison 80 % du temps ? ») a révélé un défaut de raisonnement présent depuis la phase 2.

Un bot à réglages fixes est une cible : quand il est nombreux à la table, ses copies se font concurrence et un joueur différent en profite. D'où la phase 5, un bot qui adapte son jeu en cours de partie.

Un bandit qui apprend sur ses gains ne voit que du bruit : le gain d'une manche varie d'environ 65 $ d'une donne à l'autre. Reconnaître la façon de jouer des autres marche mieux. Mais quand toutes les copies du bot reconnaissent la même table, elles changent de réglage ensemble et retombent dans la même guerre des prix.

S'entraîner contre ses propres copies corrige cette guerre des prix, mais chaque version corrige la faiblesse de la précédente et en rouvre une autre. Et les journaux de vraies parties montrent que le simulateur est loin du site : 53 échanges par manche sur figgie.com, entre 6 et 22 sur nos tables.

Rapprocher le simulateur du site ne change presque pas le classement de mes bots en simulation, mais le rejeu des vraies manches en donne un autre. Et la lecture du marché, apprise sur mes seuls bots, trouve la bonne couleur objectif dans 88 % des vraies manches à la cloche, mais se trompe en début de manche.

Sur le site, le moment d'une offre compte autant que son prix : en séparant les minutes, la lecture du marché a appris à ne pas croire les offres de la première. Face aux Hard simulés, cela rapporte 9 $ par manche au lecteur, mais ne règle pas le test de minorité.

Un score qui oublie une partie du jeu favorise les bots qui l'oublient aussi : sans la majorité, le rejeu plaçait le bayésien devant pendant deux phases. Et les plus proches voisins répondent même face à une table qui ne ressemble à rien de connu : une table de snipers, jamais vue à l'entraînement, coûtait 14 $ par manche à la v4.

Ce que mesure l'entraînement doit être ce que mesure le test : acheter à l'exploiteur rapporte 3,75 $ par carte à la copie qui achète, et coûte à l'ensemble des copies. Changer de critère réduit ce qu'il prend, mais les copies d'un bot adaptatif ne jouent pas toutes le même réglage, et leurs tables ne ressemblent pas à celles de l'entraînement.

Des copies qui s'accordent ne gagnent pas pour autant : si elles reconnaissent mal la table, elles se trompent toutes ensemble. Le profil d'une seule manche ne distingue pas la table de l'exploiteur d'une vingtaine de tables d'entraînement.

## Limites

Tous les adversaires sont des bots que j'ai écrits. Aucun chiffre de ce projet ne mesure le niveau face à des humains tant que la phase 6 (site réel) n'a pas eu lieu. Le simulateur repose sur des hypothèses : quatre règles que le site ne précise pas, et des temps de réaction inventés. Les tables ne mélangent pas encore les styles.

## Lancer le projet

Python 3.14, sans aucune dépendance externe.

```bash
cd projets/bot-figgie
python3 -m unittest                      # 142 tests, environ 15 secondes
python3 -m figgie.evaluate --candidate marginal --deals 1000 --seed 1
```

Un candidat contre tout le zoo prend quelques minutes, le tournoi de la phase 4 (`python3 -m figgie.tournoi`) environ 1 h 15 sur 10 cœurs. Chaque phase a son étiquette git (`phase0-figgie` à `phase5m-figgie`) pour retrouver le code exact.

## Stack

- Python 3.14, bibliothèque standard uniquement
- unittest pour les tests

## Statut

En cours : phases 0 à 5m terminées. Prochaine étape : garder le poids à l'achat seulement, pour que le bot ne cède plus ses cartes objectif en début de manche. La phase 6 (site réel) attend un accord écrit de Jane Street.
