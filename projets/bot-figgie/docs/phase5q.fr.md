# Phase 5q : un Hard simulé dont les offres désignent l'objectif

*English version: [phase5q.en.md](phase5q.en.md)*

La phase 5p a trouvé un écart du simulateur. Sur le site, le consensus des bots Hard trouve la couleur objectif à la cloche dans 91 % des manches, entre nos Hard simulés dans 67 à 72 % seulement. Tout ce que le bot apprend en simulation sous-estime donc ce que disent les offres d'achat. Cette phase cherche un Hard simulé plus fidèle sur ce point, en ajoutant le consensus au réglage du Hard.

Résultat : elle n'en trouve pas. Le meilleur réglage rapproche le consensus du site à la cloche (84 % au lieu de 73 %), mais il éloigne le reste du marché, et au total il fait moins bien que le Hard recalé. Lire plus fort les offres des autres ne sert à rien : les Hard se mettent tous à suivre la première couleur où quelqu'un a proposé cher, et le consensus tombe vers 30 %. Le Hard recalé reste le remplaçant de la table mixte, et aucun bot ne change. Ces mesures sont faites sur les 60 vraies manches de Rasmus et contre des bots simulés, pas sur le site.

## La mesure

Pour chaque couleur, le consensus est le plus bas des plus hauts prix d'achat proposés par les bots Hard depuis le début de la manche. Une couleur où tous ont proposé cher est probablement l'objectif. La nouvelle fonction `figgie.reel.consensus_hits` donne, à 120, 180 et 239 s, la part des manches où ce consensus met l'objectif en tête. Une égalité entre k couleurs compte pour 1/k. Sur les tables simulées, elle ne prend que trois bots Hard, comme dans les vraies manches.

Un seul seam, écrit en TDD : sur deux manches écrites à la main, la mesure donne la valeur calculée à la main. Le test échouait avant le code. Il attrape deux erreurs volontaires : compter aussi le bot de Rasmus, et compter une égalité comme une réussite entière.

`figgie.calibrate` reçoit l'option `--consensus`. Elle ajoute à l'erreur d'un réglage l'écart sur ces trois parts, à raison d'une unité d'erreur pour 5 points, comme les parts d'offres prises de la phase 5j. Elle permet aussi des forces de lecture `read` plus hautes (0,6, 0,8 et 1,2), sans changer les tirages des commandes des phases 5c et 5j.

## La recherche

Mêmes conditions qu'en phase 5j : 3 000 réglages tirés au hasard, mesurés sur 30 manches entre 4 Hard simulés (graine 31), puis les 10 meilleurs revérifiés sur 90 autres manches (graine 32), parts d'offres prises comprises.

| Mesure | figgie.com | Hard recalé (5j) | meilleur réglage (5q) |
|---|---|---|---|
| échanges par manche | 53,27 | 31,73 | 46,36 |
| échanges par paire de Hard | 9,44 | 5,29 | 7,73 |
| part des échanges par minute | 0,12 / 0,19 / 0,25 / 0,44 | 0,06 / 0,16 / 0,33 / 0,46 | 0,16 / 0,23 / 0,29 / 0,32 |
| cotations par minute | 37,75 | 58,75 | 49,50 |
| plus haute offre d'achat, objectif | 10 $ | 8 $ | 6 $ |
| plus haute offre d'achat, autres couleurs | 5 $ | 3 $ | 3 $ |
| prises d'offres hors objectif à 1-3 $ | 30 % | 25 % | 15 % |
| prises d'offres sur l'objectif à 7-10 $ | 12 % | 12 % | 9 % |
| consensus en tête à 120 / 180 / 239 s | 62 / 85 / 91 % | 62 / 69 / 73 % | 63 / 71 / 84 % |
| écart au site, sans le consensus | | 23,5 | 40,4 |
| écart au site, avec le consensus | | 46,7 | 49,5 |

Les mesures du Hard recalé sont celles de la phase 5j ; ses parts de consensus et ses deux écarts sont mesurés ici, sur les mêmes 90 manches de la graine 32.

Le meilleur réglage de la recherche échange plus, comme le site, et son consensus monte à 84 % à la cloche, contre 73 %. Mais il ne bouge pas à 180 s, il échange moins en dernière minute, il propose moins cher pour l'objectif, et il prend deux fois moins de cartes bradées que les bots du site. Au total, avec le consensus compté, il est un peu plus loin du site que le Hard recalé (49,5 contre 46,7). Les 3 000 tirages ne contenaient pas le réglage du Hard recalé, trouvé en phase 5j par une autre recherche.

## Lire plus fort ne suffit pas

Le Hard simulé lit déjà le marché : une couleur où les autres ont proposé plus cher devient plus probablement l'objectif, avec un poids exp(read × (plus haut prix proposé - moyenne sur les couleurs)). J'ai essayé, sur le Hard recalé, d'autres forces de lecture et d'autres valeurs de l'objectif (90 manches, graine 32) :

| read | valeur de l'objectif | consensus à 120 / 180 / 239 s | écart au site, sans le consensus |
|---|---|---|---|
| 0 | 16 $ | 40 / 47 / 53 % | 255,2 |
| **0,2 (Hard recalé)** | **16 $** | **62 / 69 / 73 %** | **23,5** |
| 0,4 | 16 $ | 43 / 43 / 43 % | 166,1 |
| 0,6 | 16 $ | 29 / 29 / 29 % | 167,8 |
| 1,2 | 16 $ | 30 / 30 / 30 % | 169,4 |
| 0,2 | 30 $ | 51 / 52 / 52 % | 328,4 |

Toutes les lignes sont dans `resultats/phase5q/sonde_lecture.txt`.

Sans lecture, le consensus ne trouve l'objectif qu'une fois sur deux à la cloche. Avec une lecture plus forte que 0,2, il se fige : il ne bouge plus entre 120 et 239 s. Les Hard suivent tous la première couleur où un autre a proposé cher, la font monter ensemble, et ne s'en détachent plus. Dans 70 % des manches, ce n'est pas l'objectif. Les vrais bots du site, eux, se rapprochent de l'objectif tout au long de la manche. Ils doivent tenir compte d'autre chose que des plus hautes offres d'achat, que je ne sais pas encore modéliser : les échanges, les ventes, ou ce qu'ils déduisent de leur propre main.

## Le bot progresse-t-il ?

Non : cette phase ne change aucun bot. Elle confirme que l'écart de la phase 5p vient de la structure du Hard simulé et non de son réglage. Je n'ai pas fait les étapes 4 et 5 du plan, qui supposaient un Hard v3. La v4c « achat » reste le bot de référence et le Hard recalé, le remplaçant de la table mixte.

## Limites

La recherche tire 3 000 réglages au hasard dans un espace fixé ; un meilleur réglage a pu lui échapper. Mais la sonde montre que la force de lecture, le seul réglage qui agit directement sur le consensus, ne peut pas l'amener au niveau du site.

Le consensus des vraies manches vient d'une seule table à 4 joueurs, contre le bot de Rasmus, sur 60 manches.

Le Hard simulé ne lit que les plus hautes offres d'achat. Je n'ai essayé aucune autre forme de lecture.

Tout reste mesuré sur le papier ou contre des bots simulés. Ces chiffres ne sont pas des gains réels sur figgie.com.

## Reproduire

```bash
cd projets/bot-figgie
python3 -m unittest                                                  # les 146 tests, environ 7 s
python3 -m figgie.calibrate --settings 3000 --rounds 30 --keep 10 --lift --consensus --out calibration_hard_v3.json
PYTHONPATH=. python3 resultats/phase5q/sonde_lecture.py
```

Sur 10 cœurs, la recherche et la sonde prennent chacune quelques minutes. Les sorties sont dans `resultats/phase5q/`. Pour revenir exactement au code de cette phase : `git checkout phase5q-figgie`.
