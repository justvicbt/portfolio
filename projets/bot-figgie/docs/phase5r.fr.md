# Phase 5r : un Hard simulé avec un indice privé

*English version: [phase5r.en.md](phase5r.en.md)*

La phase 5q a montré qu'on ne rend pas notre Hard simulé plus fidèle au site en lui faisant lire plus fort les plus hautes offres d'achat des autres. Dans cette phase, je regarde d'abord à quoi réagissent vraiment les bots Hard du site. Je modélise ensuite ce que je vois, sans savoir d'où ça vient : chacun d'eux semble savoir de mieux en mieux, au fil de la manche, quelle couleur est l'objectif.

Le Hard v3 reçoit donc un indice privé sur l'objectif, dont le poids monte avec le temps. Réglé sur les vraies manches, il ressemble deux fois plus au site que le Hard recalé, consensus compris. La v4c « achat » passe toujours la règle d'entrée avec lui à la table mixte, et il devient le remplaçant de cette table pour les phases suivantes. Aucun bot de jeu ne change. Les mesures sont faites sur les 60 vraies manches de Rasmus et contre des bots simulés, pas sur le site.

## À quoi réagissent les bots du site

Je regarde un moment précis : un bot Hard propose dans une couleur un prix d'achat plus haut que tout ce qu'il y avait proposé depuis le début de la manche, un « record ». Après chaque événement venu d'un autre joueur dans la même couleur, je compte les records des autres bots Hard dans les 10 s qui suivent. Je divise ce nombre par ce qu'on attendrait au hasard, au rythme de records de ce bot dans cette couleur et dans cette minute. Un rapport de 1 veut dire « aucune réaction ».

| Événement dans la couleur | vraies manches : objectif | autre couleur | Hard recalés : objectif | autre couleur |
|---|---|---|---|---|
| échange à 1-3 $ | aucun | 1,12 | 1,34 | 1,33 |
| échange à 4-6 $ | 1,24 | 1,01 | 1,10 | 0,89 |
| échange à 7 $ et plus | 0,99 | 0,96 | 0,76 | 0,76 |
| offre de vente affichée | 1,00 | 0,93 | 0,97 | 0,98 |
| retrait d'une offre | 1,15 | 1,42 | 1,42 | 1,70 |
| offre d'achat record de la table | 1,00 | 1,13 | 1,39 | 1,57 |

Les Hard recalés jouent ici 200 manches simulées contre la v4c « achat », avec la règle du site (graine 9). Le nombre de cas de chaque case est dans `resultats/phase5r/reactions.txt`.

Les bots du site ne réagissent presque à rien de ce qui est public. Leurs rapports restent proches de 1, sauf après un retrait, un événement rare : 233 en 60 manches (phase 5p). Nos Hard recalés, eux, suivent les records des autres : 1,39 et 1,57. C'est leur lecture du marché, et c'est elle qui fige le consensus quand on la renforce (phase 5q). Un détail aussi : sur le site, aucun échange de l'objectif ne se fait à 1-3 $ en 60 manches.

## Chaque bot pris seul

Si les bots du site ne lisent pas les autres, d'où vient leur consensus ? J'ai pris chaque bot Hard seul. À chaque instant, je regarde la couleur où il a proposé son plus haut prix d'achat dans les 30 dernières secondes, et je compte la part des cas où c'est l'objectif. Une égalité entre k couleurs compte pour 1/k, et le hasard donne 25 %.

| Plus haute offre d'un bot sur les 30 dernières s | 60 s | 120 s | 180 s | 239 s |
|---|---|---|---|---|
| vraies manches | 27 % | 57 % | 80 % | 76 % |
| Hard recalés | 51 % | 55 % | 57 % | 64 % |

Un bot du site ne sait rien de plus que le hasard à 60 s, puis trouve l'objectif de mieux en mieux, jusqu'à 80 % à 180 s. Nos Hard recalés en savent plus au début, par leur main, puis presque plus rien ne change. Chaque vrai bot reçoit donc au fil de la manche une information sur l'objectif que les nôtres n'ont pas. Elle ne vient pas du marché public, d'après le tableau précédent. Je ne sais pas ce que c'est : une règle du site, une lecture des échanges que je n'ai pas vue, autre chose. Je l'ai donc modélisée telle qu'on la voit, sans prétendre savoir comment le site fait.

## Le Hard v3

Le moteur donne maintenant l'objectif aux seuls bots qui le demandent (`sees_goal`). Le Hard v3 (`HardBotV3`, `hard_simule_v3`) s'en sert comme d'un indice. Le Hard simulé estime déjà la probabilité que chaque couleur soit l'objectif, à partir de sa main et des offres des autres. Le Hard v3 multiplie ces poids par :

- (1 - λ) / 4 + λ pour l'objectif ;
- (1 - λ) / 4 pour les autres couleurs ;
- avec λ = min(1, t / hint_time) ^ hint_power.

À t = 0, l'indice ne dit rien. À t = hint_time, il désigne l'objectif à coup sûr. Entre les deux, il monte d'autant plus tard que hint_power est grand.

Un seul seam, écrit en TDD, avec deux tests :
- à t = 0, le Hard v3 donne les mêmes valeurs qu'un Hard ordinaire de même réglage, et à t = hint_time, il connaît l'objectif ;
- le moteur ne donne l'objectif qu'aux bots qui le demandent.

Les deux tests échouaient avant le code. Ils attrapent trois erreurs volontaires : ignorer l'indice, donner à λ une valeur fixe, ne pas transmettre l'objectif. Les Hard v1 et v2 ne changent pas, et le test des parties enregistrées passe toujours.

## Le réglage

`figgie.calibrate` reçoit l'option `--hint`, qui règle le Hard v3 avec deux paramètres de plus : hint_time parmi 60, 120, 180, 240, 300 et 400 s, et hint_power parmi 0,5, 1, 2 et 3. Les conditions sont celles de la phase 5q : 3 000 réglages tirés au hasard, mesurés sur 30 manches entre 4 Hard v3 (graine 31), puis les 10 meilleurs revérifiés sur 90 autres manches (graine 32), parts d'offres prises et consensus compris.

Avant de lancer la recherche, j'avais fixé le critère : le Hard v3 n'est retenu que si son écart au site, consensus compris, passe sous les 46,7 du Hard recalé, avec un consensus d'au moins 85 % à la cloche.

| Mesure | figgie.com | Hard recalé (5j) | Hard v3 (5r) |
|---|---|---|---|
| échanges par manche | 53,27 | 31,73 | 36,23 |
| échanges par paire de Hard | 9,44 | 5,29 | 6,04 |
| part des échanges par minute | 0,12 / 0,19 / 0,25 / 0,44 | 0,06 / 0,16 / 0,33 / 0,46 | 0,17 / 0,20 / 0,25 / 0,38 |
| cotations par minute | 37,75 | 58,75 | 57,38 |
| plus haute offre d'achat, objectif | 10 $ | 8 $ | 9 $ |
| plus haute offre d'achat, autres couleurs | 5 $ | 3 $ | 4 $ |
| prises d'offres hors objectif à 1-3 $ | 30 % | 25 % | 21 % |
| prises d'offres sur l'objectif à 7-10 $ | 12 % | 12 % | 10 % |
| consensus en tête à 120 / 180 / 239 s | 62 / 85 / 91 % | 62 / 69 / 73 % | 59 / 76 / 96 % |
| écart au site, avec le consensus | | 46,7 | **23,5** |

Le critère est rempli. Le réglage retenu est dans `figgie/bots.py` et dans `resultats/phase5r/calibration_hard_v3.md` : hint_time = 400 s et hint_power = 2. À la cloche, l'indice ne pèse donc que (240 / 400)² = 0,36. La recherche a choisi un indice lent et presque plus de lecture des autres (read = 0,05 au lieu de 0,2). Le meilleur réglage suivant est à 34,4.

Pris seul, le Hard v3 se rapproche aussi du site sur le tableau précédent :

| Plus haute offre d'un bot sur les 30 dernières s | 60 s | 120 s | 180 s | 239 s |
|---|---|---|---|---|
| vraies manches | 27 % | 57 % | 80 % | 76 % |
| Hard v3 | 41 % | 58 % | 75 % | 86 % |

Il reste des écarts. Il en sait trop à 60 s, par sa main, et un peu trop à la cloche. Il échange encore moins que le site. Il prend aussi deux fois plus d'offres hors objectif à 4-6 $ (13 % contre 6 %).

## Ce que ça change pour la lecture du site

La phase 5p s'était arrêtée sur une lecture avec une atténuation par minute, choisie en simulation, qui ne faisait pas mieux sur les vraies manches. J'ai relancé le même prototype, avec des manches de validation jouées avec le Hard v3 (1 000 manches, graine 52). Les atténuations choisies montent en fin de manche : 0,5, 0,5, 0,5 puis 1,0. Le tableau donne la probabilité de la vraie couleur, la part en tête et la perte log, sur les vraies manches :

| Vraies manches | 120 s | 180 s | 225 s | 239 s |
|---|---|---|---|---|
| aujourd'hui (0,2 partout) | 0,41 ; 53 % ; 1,031 | 0,63 ; 77 % ; 0,610 | 0,78 ; 85 % ; 0,406 | 0,81 ; 85 % ; 0,360 |
| choisie avec le Hard v3 | 0,49 ; 63 % ; 1,053 | 0,76 ; 83 % ; 0,547 | 0,86 ; 87 % ; 0,621 | 0,86 ; 85 % ; 0,547 |

Avec le Hard v3, la lecture choisie en simulation fait mieux sur les vraies manches à 120 et 180 s, ce qui n'arrivait pas en 5p. En fin de manche, elle trouve un peu plus souvent la bonne couleur mais se trompe avec trop d'assurance : sa perte log monte de 0,360 à 0,547 à la cloche. Le modèle de signaux qu'elle utilise a été appris en phase 5d, sur des tables avec le Hard de la phase 5c. Il faudra sans doute le réapprendre avant de changer quoi que ce soit dans le bot. Je n'ai rien codé dans le dépôt pour cette lecture.

## Le tournoi avec le Hard v3 à la table mixte

J'ai rejoué le tournoi réduit de la phase 5n pour la v4c « achat » (10 manches, 100 donnes, règle du site), avec le Hard v3 comme remplaçant de la table mixte au lieu du Hard recalé. Les tables sans remplaçant gardent les chiffres de la 5n, puisque les donnes sont les mêmes. Contre trois Hard du même type :

| v4c « achat » contre | 4 j. | 5 j. |
|---|---|---|
| hard_simule_v2 | +17,58 [+16,00 ; +19,16] | +15,91 [+14,55 ; +17,27] |
| hard_simule_v3 | +34,76 [+33,31 ; +36,21] | +33,38 [+31,94 ; +34,82] |

À la table mixte, l'écart référence moins v4c « achat », en dollars par manche (négatif : la v4c « achat » fait mieux) :

| Référence | 4 j., Hard recalé | 4 j., Hard v3 | 5 j., Hard recalé | 5 j., Hard v3 |
|---|---|---|---|---|
| marginal | -18,88 | -46,51 | -13,42 | -39,30 |
| adaptatif_v3 | -13,45 | -44,39 | -10,22 | -38,99 |
| exploiteur_lecteur | -10,99 | -37,47 | +0,34 [-1,08 ; +1,75] | -31,26 [-32,68 ; -29,85] |
| adaptatif_v4b | -13,25 | -11,31 | -7,53 | -5,00 |
| adaptatif_v4c | -15,64 | -8,55 | -8,82 | -4,84 |
| v4c_calme_60 | -3,85 [-5,12 ; -2,57] | -4,68 [-5,78 ; -3,59] | -1,85 [-3,02 ; -0,67] | -3,79 [-4,73 ; -2,86] |
| v4c_temps | -4,45 [-5,56 ; -3,33] | -3,85 [-4,59 ; -3,12] | -3,29 [-4,15 ; -2,43] | -2,18 [-2,95 ; -1,40] |

Toutes les lignes, intervalles de confiance à 95 % compris, sont dans `resultats/phase5r/tournoi_hard_v3.md`.

La v4c « achat » passe la règle d'entrée aux deux tailles : aucun écart n'a son intervalle entier au-dessus de 0. Avec le Hard v3, les offres d'achat désignent vraiment l'objectif. Les bots qui lisent le marché, ceux de la famille v4c, restent proches de la v4c « achat ». Ceux qui ne le lisent pas, ou mal, perdent 25 à 30 $ de plus par manche. Le cas le plus net est l'exploiteur lecteur à 5 joueurs, le bot le plus proche d'elle dans le tournoi de la phase 5n : il était à égalité avec la v4c « achat », il perd maintenant 31 $ par manche.

Un point m'inquiète. La v4c « achat » bat trois Hard v3 de 35 $ par manche, deux fois plus que trois Hard recalés. Je n'ai pas encore regardé d'où vient ce gain. Les vraies manches ne disent pas si les bots du site se laissent faire autant.

## Le Hard v3 devient le remplaçant

Changer de remplaçant déplace toutes les mesures des phases suivantes. Je ne l'ai fait qu'après avoir montré ces chiffres et posé la question. `figgie.tournoi --mixed` prend maintenant le Hard v3 par défaut. Pour refaire les tournois des phases 5j à 5q, il faut ajouter `--filler hard_simule_v2`.

## Le bot progresse-t-il ?

Non, cette phase ne change aucun bot de jeu. Elle rend le simulateur plus proche du site sur le point que la phase 5p avait trouvé. La v4c « achat » reste le bot de référence et passe la règle d'entrée avec le nouveau remplaçant. Les écarts avec ses variantes bougent de 1 à 7 $, et elle reste devant chacune.

## Limites

Le Hard v3 triche : le moteur lui donne l'objectif. Je reproduis ce que les bots du site semblent savoir, sans savoir comment ils le savent. Si leur information vient d'ailleurs, par exemple de leur propre lecture des échanges, le Hard v3 peut se tromper sur la façon dont elle réagit au jeu de notre bot.

Le réglage reste imparfait. Le Hard v3 en sait trop en début de manche, échange moins que le site, et prend trop d'offres hors objectif à 4-6 $.

La v4c « achat » le bat de 35 $ par manche. S'il est plus facile à exploiter que les vrais bots, les tournois surestimeront les bots qui l'exploitent.

Le réglage vient d'une seule table à 4 joueurs, contre le bot de Rasmus, sur 60 manches. Rien ne dit que le Hard v3 se comporte comme le site à 5 joueurs.

Le modèle de signaux de la lecture du site n'a pas été réappris avec le Hard v3.

Tout reste mesuré sur le papier ou contre des bots simulés. Ces chiffres ne sont pas des gains réels sur figgie.com.

## Reproduire

```bash
cd projets/bot-figgie
python3 -m unittest                                                  # les 148 tests, environ 7 s
PYTHONPATH=. python3 resultats/phase5r/reactions.py
PYTHONPATH=. python3 resultats/phase5r/individuel.py
python3 -m figgie.calibrate --settings 3000 --rounds 30 --keep 10 --lift --consensus --hint --out resultats/phase5r/calibration_hard_v3.json
PYTHONPATH=. python3 resultats/phase5r/attenuation_v3.py 1000
python3 -m figgie.tournoi --site --candidates v4c_achat --rounds 10 --deals 100 --no-tables --filler hard_simule_v3 \
  --opponents heuristique sniper bayesien marginal hard_simule hard_simule_v2 hard_simule_v3 --references \
  --mixed hard_simule_v2 bayesien marginal adaptatif_v3 adaptatif_v4b adaptatif_v4c v4c_calme_60 v4c_vente_60 \
          exploiteur exploiteur_lecteur vendeur parieur v4c_temps \
  --out resultats/phase5r/tournoi_hard_v3.json
```

Sur 10 cœurs, la recherche prend environ 5 min, les diagnostics quelques minutes chacun et le tournoi environ 2 h 30. Les sorties sont dans `resultats/phase5r/`. Pour revenir exactement au code de cette phase : `git checkout phase5r-figgie`.
