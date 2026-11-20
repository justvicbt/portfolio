# Phase 5 : adaptation en cours de partie

*English version: [phase5.en.md](phase5.en.md)*

La phase 4 s'est terminée sur un constat : un bot à réglages fixes est une cible. Quand le marginal cote à 8 $ de sa valeur, un adversaire qui cote à 6 $ prend tout le flux. Quand il resserre, ses copies se font concurrence et même un joueur aléatoire en profite. Cette phase essaie de sortir du dilemme avec un bot qui choisit son spread et sa marge manche après manche, selon la table qu'il a en face.

Le bilan est partagé. Le bot adaptatif bat le marginal en tête-à-tête, à 4 comme à 5 joueurs, et l'exploiteur de la phase 4 lui prend beaucoup moins. Mais il ne passe pas le test de minorité : un sniper seul face à trois de ses copies gagne 3,72 $ par manche, alors qu'il perdait face au marginal. La recherche automatique trouve même un preneur qui lui prend 5,62 $ par manche. Aucun bot n'est promu. Et la raison de l'échec est instructive : toutes les copies reconnaissent la même table et prennent la même décision au même moment.

## Pourquoi pas un bandit sur les gains

La fin de la phase 4 proposait un bandit : essayer un réglage, regarder ce qu'il rapporte, privilégier ce qui marche. Avant d'écrire une ligne, j'ai fait le calcul, et il ne tient pas. Le gain d'une manche varie d'environ 65 $ d'une donne à l'autre, parce que la donne elle-même décide en grande partie qui gagne. Deux réglages voisins, eux, ne diffèrent que de quelques dollars par manche. Pour les départager avec un intervalle de confiance honnête, il faudrait environ 700 manches par réglage. Une partie en compte une dizaine. Un bandit qui apprend sur ses gains passerait donc toute la partie à mesurer du bruit.

J'ai donc retenu l'autre voie : reconnaître la table. Le comportement des autres joueurs, lui, est peu bruité. En une manche, on voit déjà à quelle vitesse ils cotent, à quel écart, s'ils restent muets. Le bot apprend hors ligne, en simulation et en donnes dupliquées (donc sans le bruit de la donne), quel réglage marche contre quel type de table. En partie, il mesure la table, cherche les tables d'entraînement qui lui ressemblent le plus et joue le réglage qui y marchait le mieux.

## La méthode

Le bot adaptatif garde tout le calcul de valeur du marginal. Seuls deux nombres changent : son spread et sa marge de prise. Il choisit entre quatre réglages : (6 $, 3 $), (8 $, 1 $), (10 $, 3 $) et (12 $, 3 $). Le deuxième est celui du marginal, et c'est par lui que le bot commence chaque partie, puisqu'il ne sait encore rien de la table.

Le profil d'une table tient en six nombres, calculés à partir du fil public des événements :

- combien de cotations par minute les autres postent, en moyenne et pour le plus actif ;
- l'écart le plus serré et l'écart médian quand un joueur cote des deux côtés d'une couleur ;
- le temps minimum qu'un joueur met à recoter après un échange ;
- la part des joueurs qui ne cotent jamais.

Pour apprendre, j'ai tiré 80 tables d'entraînement à 4 ou 5 joueurs, avec des adversaires pris dans le zoo et parmi les menteurs (graine 9). Les tables pleines de marginaux y sont surreprésentées, parce que c'est là que des copies se font concurrence, le cas que le test de minorité punit. Sur chaque table, j'ai mesuré le gain de chacun des quatre réglages sur 100 donnes dupliquées. En partie, le bot compare le profil de sa table à ceux des 80 tables, en ramenant chaque mesure à la même échelle, prend les 5 plus proches et choisit le réglage qui y rapporte le plus en moyenne. Le réglage est fixé au début de chaque manche et ne bouge plus jusqu'à la fin.

Pour suivre les cotations, le bot avait besoin de voir quand un joueur retire la sienne. Le fil public du marché annonce maintenant les annulations. Ça ne change rien au jeu des autres bots, et le test de référence de la phase 4 le confirme.

## Version 1, puis version 2 après relecture

La première version a été validée sur 30 tables jamais vues (graine 10). Le réglage fixe y rapporte 17,49 $ par manche, le réglage choisi 18,02 $, et le meilleur réglage possible, qu'on ne peut connaître qu'après coup, 18,89 $. Le gain sur le fixe est de 0,52 $ par manche, avec un intervalle de [+0,05 ; +0,99]. Petit, mais net.

La relecture du code a trouvé un problème plus sérieux que tous les autres. En entraînement, le profil de chaque table était mesuré sur 10 manches, en jouant toujours le réglage de référence. En partie, le bot n'a qu'une ou deux manches derrière lui, et il les a jouées avec ses propres réglages. Il apprenait donc sur des profils qu'il ne voit jamais en jouant. La relecture a aussi relevé six défauts plus petits : la table des menteurs était jouée deux fois avec plusieurs manches, le chemin du modèle n'était pas réglable, le cache du modèle ignorait le fichier, les options de la recherche d'exploiteurs n'étaient pas vérifiées, les graines pouvaient se chevaucher au-delà de 1 000 tables, et un test ne vérifiait pas ce qu'il annonçait. Tous sont corrigés.

Pour la version 2, j'ai mesuré sur chaque table d'entraînement 10 profils d'une seule manche, avec chacun des quatre réglages. En partie, chaque manche jouée donne un profil, mesuré avec le réglage que le bot jouait, et le bot fait la moyenne des recommandations de chacune. Je l'ai validée par validation croisée sur les 80 tables : chaque table est jugée par un modèle construit sur les 79 autres.

| Choix du réglage | Gain moyen | Écart au réglage fixe |
|---|---|---|
| fixe (8, 1) | +16,88 | |
| v1, profil de 10 manches (ce qui était validé) | +17,13 | +0,25 [-0,04 ; +0,54] |
| v1, après 1 manche (ce qu'elle voit vraiment) | +17,00 | +0,12 [-0,20 ; +0,44] |
| v1, après 3 manches | +16,95 | +0,07 [-0,30 ; +0,44] |
| v2, après 1 manche | +17,00 | +0,11 [-0,24 ; +0,47] |
| v2, après 3 manches | +17,27 | +0,38 [+0,13 ; +0,64] |
| meilleur réglage, connu après coup | +17,77 | +0,89 [+0,65 ; +1,12] |

En dollars par manche. La relecture avait raison : la v1, telle qu'elle joue vraiment, ne fait plus nettement mieux que le réglage fixe. La v2, après trois manches, récupère un peu moins de la moitié de ce qu'on pourrait gagner en connaissant la réponse.

## Le tournoi

Le bot adaptatif a besoin de plusieurs manches pour s'adapter. Le tournoi se joue donc en parties de 10 manches, sur 300 donnes dupliquées (graine 1), soit 3 000 manches par adversaire. Le marginal a été remesuré dans les mêmes conditions, pour une comparaison directe. Les deux exploiteurs de la phase 4 entrent aussi dans le test de minorité.

| | marginal | adaptatif v1 | adaptatif v2 |
|---|---|---|---|
| contre le marginal, 4 j. | | +1,94 [+1,58 ; +2,30] | +2,00 [+1,64 ; +2,37] |
| contre le marginal, 5 j. | | +3,45 [+3,13 ; +3,78] | +3,47 [+3,15 ; +3,79] |
| contre le lecteur, 4 j. | +0,97 | +2,33 | +2,21 |
| contre le lecteur, 5 j. | +5,52 | +8,52 | +8,33 |
| contre l'exploiteur, 4 j. | +19,84 | +18,53 | +17,14 |
| sniper seul, 4 j. | -0,94 [-1,39 ; -0,48] | +3,55 [+3,06 ; +4,03] | +3,72 [+3,24 ; +4,21] |
| sniper seul, 5 j. | -1,28 [-1,64 ; -0,91] | +2,66 [+2,27 ; +3,05] | +2,80 [+2,42 ; +3,19] |
| bayésien seul, 4 j. | +1,14 [+0,56 ; +1,72] | +0,99 [+0,41 ; +1,57] | +0,10 [-0,47 ; +0,67] |
| marginal seul, 4 j. | | +1,25 [+0,91 ; +1,58] | +1,29 [+0,95 ; +1,64] |
| marginal seul, 5 j. | | -0,32 [-0,64 ; -0,00] | -0,26 [-0,56 ; +0,04] |
| exploiteur seul, 4 j. | +4,32 [+3,85 ; +4,80] | +1,63 [+1,14 ; +2,11] | +1,54 [+1,06 ; +2,02] |
| exploiteur seul, 5 j. | +7,24 [+6,85 ; +7,64] | +3,16 [+2,79 ; +3,54] | +3,02 [+2,64 ; +3,39] |

En dollars par manche. Les lignes « seul » donnent le gain de l'adversaire seul face aux copies du candidat : plus il est haut, plus le candidat se fait exploiter.

Contre le reste du zoo, rien ne bouge : les trois bots gagnent nettement contre chaque adversaire, à quelques dizaines de centimes près. Aux tables anormales (100 donnes, 10 manches), les chiffres sont proches eux aussi : +20,4 $ avec le joueur inactif pour les trois, +20,4 $ avec les menteurs pour le marginal et la v2 (+19,3 $ pour la v1), et +119,6 $ avec le spammeur pour le marginal et la v2 (+112,4 $ pour la v1).

**Le verdict de la règle d'entrée.** Les trois bots battent nettement tout le zoo. Aucun ne passe le test de minorité. Le marginal échoue à 4 joueurs (bayésien seul, +1,14 $), et à 5 joueurs à cause de l'exploiteur, maintenant que les exploiteurs comptent dans le test. Les deux adaptatifs échouent à 4 et à 5 joueurs, à cause du sniper seul, et à 4 joueurs aussi à cause du marginal seul. Aucun bot n'est promu, le marginal reste la référence.

**Le bot s'améliore-t-il ?** En partie, oui. Il bat le marginal en tête-à-tête, de 2 $ par manche à 4 joueurs et de 3,5 $ à 5. Il gagne plus contre le lecteur. L'exploiteur de la phase 4 lui prend moins de la moitié de ce qu'il prenait au marginal. Mais il a ouvert une faiblesse nouvelle : le sniper, qui ne gagnait rien seul face aux marginaux, gagne maintenant nettement face aux adaptatifs. La v2 fait à peu près jeu égal avec la v1 partout. Sa meilleure validation hors ligne ne se voit pas dans le tournoi.

## Pourquoi le sniper gagne

J'ai regardé quels réglages choisissent trois adaptatifs face à un sniper seul. Dès la deuxième manche, ils passent tous les trois au spread de 6 $, et ils y restent. C'est logique de leur point de vue : leur table ressemble aux tables d'entraînement remplies de marginaux, et sur ces tables, coter à 6 $ est exactement ce que faisait l'exploiteur de la phase 4. Seulement, sur les tables d'entraînement, le bot était le seul à resserrer. Ici, ses trois copies le font en même temps. On retombe dans la guerre des prix de la phase 4 : trois bots qui cotent serré se disputent les mêmes cartes, et le sniper, qui ne fait que prendre les prix mal placés, en profite.

Le défaut vient de l'entraînement. Le bot n'a jamais vu de table où les autres s'adaptent comme lui. Il a appris la meilleure réponse à des adversaires fixes, et il l'applique à des adversaires qui changent au même moment que lui.

## Exploiteurs

J'ai relancé la recherche d'exploiteurs de la phase 4 contre la v2, à 4 joueurs, en parties de 10 manches. Chaque étape coûte dix fois plus cher qu'avant, alors j'ai réduit le nombre de donnes : 20 à l'étape 1 (graine 5), 100 à l'étape 2 (graine 6) et 300 à l'étape 3 (graine 1). Les 60 réglages essayés restent les mêmes.

Le gagnant est un preneur pur. Il calcule ses valeurs comme le marginal, ne cote jamais, prend toute cotation qui lui laisse au moins 2 $ de marge, et réagit en 0,2 seconde. C'est un sniper mieux informé. Seul face à trois copies de la v2, il gagne +5,62 $ par manche [+5,16 ; +6,08]. C'est plus que ce que l'exploiteur de la phase 4 prenait au marginal (+4,32 $).

Je l'ai ensuite mesuré contre les autres candidats, sur les mêmes 300 donnes :

| Seul face à des copies de | 4 joueurs | 5 joueurs |
|---|---|---|
| marginal | -0,70 [-1,11 ; -0,29] | -1,30 [-1,69 ; -0,92] |
| adaptatif v1 | +5,44 [+4,98 ; +5,90] | +4,14 [+3,70 ; +4,58] |
| adaptatif v2 | +5,62 [+5,16 ; +6,08] | |

Gain du preneur, en dollars par manche.

Ce tableau confirme le diagnostic. Contre le marginal, qui garde son spread de 8 $, le preneur perd. Contre les adaptatifs, il gagne nettement. C'est l'adaptation elle-même, quand toutes les copies resserrent ensemble, qui crée la faiblesse. Je n'ai pas eu le temps de lancer la recherche à 5 joueurs.

## Ce que j'en retiens

Faire le calcul avant de coder m'a évité un bandit qui n'aurait rien appris. Avec 65 $ de bruit par manche, une partie de 10 manches ne dit presque rien du réglage qu'on a joué. Ce qui se mesure vite, c'est la façon de jouer des autres.

La relecture du code a trouvé le défaut le plus important de la phase, et c'était un défaut de méthode. Un bot entraîné sur des mesures qu'il ne verra jamais en jouant fait illusion en validation. Il faut mesurer l'entraînement exactement comme le bot le vivra.

S'adapter à la table ne suffit pas quand la table s'adapte aussi. Une meilleure réponse apprise contre des adversaires fixes devient une faiblesse dès que les autres joueurs suivent la même règle. En théorie des jeux, c'est la différence entre répondre au mieux à des stratégies connues et chercher un équilibre. La suite logique serait d'entraîner le bot sur des tables où se trouvent aussi ses propres copies, puis de recommencer avec la nouvelle version, jusqu'à ce que ses choix ne changent plus.

## Limites

Tous les adversaires sont toujours des bots. Les gains mesurés ici, contre des bots simulés, ne disent rien du niveau face à des humains.

Le bot choisit entre quatre réglages seulement, avec un modèle appris sur 80 tables. Il n'apprend rien d'une partie à l'autre : il s'adapte à l'intérieur d'une partie, avec un modèle construit une fois hors ligne. Il ne lit pas non plus le marché comme le lecteur de la phase 3.

Le tournoi porte sur 300 donnes au lieu de 1 000, parce que chaque donne est maintenant une partie de 10 manches. Les intervalles restent de l'ordre du dollar.

Les limites des phases précédentes tiennent toujours : temps de réaction inventés, quatre règles du site supposées, argent qui repart de 350 $ à chaque manche.

## Reproduire

```bash
cd projets/bot-figgie
python3 -m unittest                                                  # les 97 tests, environ 5 s
python3 -m figgie.adapt --tables 80 --valid 30 --deals 100 --report adaptation.json   # version 1
python3 -m figgie.adapt --tables 80 --deals 100 --v2-from adaptation.json --report adaptation_v2.json
python3 -m figgie.tournoi --candidates marginal adaptatif adaptatif_v2 --rounds 10 --deals 300 --table-deals 100 \
    --references heuristique sniper bayesien marginal exploiteur exploiteur_lecteur --out tournoi.json
python3 -m figgie.exploit --target adaptatif_v2 --players 4 --rounds 10 --deals 20 100 300
```

Le tournoi prend environ une heure et demie par candidat sur 10 cœurs. Pour revenir exactement au code de cette phase : `git checkout phase5-figgie`.

## Et ensuite

La phase 6 est le site réel, et elle attend un accord écrit de Jane Street. D'ici là, deux pistes restent ouvertes en local. La première corrige le défaut trouvé ici : entraîner le bot adaptatif sur des tables qui contiennent ses propres copies, et répéter jusqu'à ce que ses choix se stabilisent. La seconde combine l'adaptation avec la lecture du marché de la phase 3, qui n'est pas encore utilisée par le bot adaptatif.
