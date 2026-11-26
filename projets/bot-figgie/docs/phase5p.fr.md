# Phase 5p : ce que le bot croit des autres

*English version: [phase5p.en.md](phase5p.en.md)*

Cette phase ne contient que des mesures. Je voulais savoir si la v4c « achat », le bot de référence depuis la phase 5n, laisse passer la carte qui départage une égalité de majorité, une idée de la v5 de Rasmus Suonio. Elle la laisse passer, mais pas à cause du calcul de sa valeur, qui compte déjà ce gain. Il lui manque de l'information : quelle couleur est l'objectif, et combien de cartes objectif ont ses rivaux. J'ai alors essayé de mieux lire la couleur en fin de manche, et je me suis arrêté comme le plan le prévoyait : la nouvelle lecture ne faisait pas mieux sur les vraies manches. La cause est dans le simulateur. Les offres d'achat de nos Hard simulés désignent l'objectif bien moins souvent que celles des vrais bots du site.

Aucun bot ne change, aucun tournoi n'est joué. Toutes les mesures sont faites contre des bots simulés ou sur les 60 vraies manches de Rasmus, pas sur le site.

## Le regroupement

À 4 joueurs, si l'objectif a 10 cartes et que deux joueurs en ont 5 chacun, ils se partagent le reste du pot. Une sixième carte donne tout le pot à celui qui l'a : elle vaut alors bien plus que 10 $. Rasmus en a fait une règle de son bot.

J'ai fait jouer la v4c « achat » contre des Hard recalés, sur 200 parties de 10 manches à chaque taille de table (graine 9, règle du site, le bot à un siège différent selon la donne). En fin de manche, je classe sa position dans la couleur objectif face au meilleur rival :

| Position finale | 4 j. : part des manches | gain moyen | 5 j. : part des manches | gain moyen |
|---|---|---|---|---|
| seul en tête | 37,8 % | +90,27 $ | 27,9 % | +100,21 $ |
| à égalité | 13,4 % | +33,70 $ | 9,4 % | +44,75 $ |
| une carte derrière | 1,1 % | -18,62 $ | 1,1 % | -12,38 $ |
| plus loin | 47,8 % | -38,93 $ | 61,7 % | -26,75 $ |

Le bot finit rarement à une carte près. Quand il ne gagne pas la majorité, il n'a presque plus de carte objectif : 0,23 en moyenne à 4 joueurs, 0,09 à 5. Il les a vendues. Les égalités, elles, sont fréquentes, surtout quand l'objectif a 10 cartes : 17,8 % de ces manches à 4 joueurs, 11,9 % à 5. C'est exactement le cas de Rasmus.

Dans une manche finie à égalité, une carte objectif de plus lui aurait rapporté environ 61 $, si plus rien d'autre n'avait changé. Et dans toutes ces manches, un autre joueur a affiché après 120 s une offre de vente sur l'objectif moins chère que ce gain. À 4 joueurs, la moins chère valait 16,41 $ en moyenne, alors que la meilleure offre d'achat du bot sur l'objectif était de 10,73 $. À 5 joueurs, 17,15 $ contre 9,84 $.

Le gain possible est au plus d'environ 6 $ par manche à 4 joueurs et 4 $ à 5. C'est une borne haute : je la calcule en connaissant la fin de la manche, et les rivaux réagiraient si le bot achetait.

## Pourquoi il ne paie pas cette carte

La valeur du bot compte en principe ce gain : pour chaque monde tiré au hasard, elle calcule le gain exact d'une carte de plus, égalités comprises. J'ai donc recalculé cette valeur au moment de chaque offre de vente sur l'objectif vue après 120 s, dans les manches finies à égalité (100 parties à chaque taille). Je compare quatre valeurs de la même carte, au même instant :
- A, celle du bot ;
- B, la même sans le poids du temps de la phase 5n ;
- C, B avec l'objectif connu : seules les mains des rivaux restent cachées ;
- D, le gain exact, mains de tous connues, si plus rien ne s'échange.

Pour les offres moins chères que D :

| | 4 j. | 5 j. |
|---|---|---|
| offres | 2 501 | 2 126 |
| prix moyen | 27,60 $ | 27,25 $ |
| A, le bot | 10,26 $ | 10,87 $ |
| B, sans le poids du temps | 10,93 $ | 11,62 $ |
| C, objectif connu | 20,98 $ | 18,39 $ |
| D, tout connu | 60,46 $ | 61,59 $ |
| part des offres qu'il prendrait avec A | 1 % | 1 % |
| avec C | 25 % | 14 % |

Une offre compte ici chaque fois que la meilleure offre de vente sur l'objectif change, si bien qu'une manche en donne plusieurs.

Le poids du temps n'y est pour presque rien : il retire moins d'un dollar. Ne pas savoir quelle couleur est l'objectif divise la valeur par deux. Le reste vient des mains cachées : même en connaissant l'objectif, le bot ne voit pas qu'un rival est à égalité avec lui, et il estime la carte au tiers de ce qu'elle vaut. Le regroupement est donc déjà dans le calcul. Ce qui manque, c'est l'information sur laquelle il porte.

## Ce qu'il croit des autres

J'ai noté ce que croit le bot à 120, 180 et 225 s, sur 100 parties à chaque taille, et je l'ai comparé à la vérité. À 225 s, dans les manches finies à égalité :

| | 4 j. | 5 j. |
|---|---|---|
| probabilité donnée à la vraie couleur objectif | 0,73 | 0,79 |
| part des manches où il la met en tête | 80 % | 78 % |
| cartes objectif du rival en tête : vraies | 4,49 | 4,30 |
| attendues par le bot | 3,02 | 2,92 |
| dont cartes qu'il connaît (achats et ventes proposées) | 1,89 | 1,95 |

Le bot place les cartes qu'il ne voit pas au hasard dans les mains des rivaux. En moyenne sur les rivaux, c'est juste, puisque le total est connu. Mais le rival en tête a souvent reçu beaucoup de cartes objectif à la donne, et rien dans le calcul ne le laisse voir. Le bot le croit à 3 cartes quand il en a 4 ou 5.

Pour mieux estimer ces mains, il faudrait lire ce que les offres d'un rival disent de sa donne. Les journaux de Rasmus ne donnent pas les mains des bots du site : un tel modèle ne pourrait être vérifié que contre nos Hard simulés, au risque d'apprendre leurs tics. La couleur objectif, elle, se vérifie sur les vraies manches. C'est donc par elle que j'ai commencé.

## Les bots du site retirent-ils leurs offres ?

C'était la dernière vérification de l'audit de la phase 5m. Dans les 60 vraies manches, les trois bots Hard retirent 233 offres, dans 40 manches sur 60. C'est 0,86 % de leurs 27 009 cotations. Ils retirent presque toujours un seul côté (227 fois, contre 3 fois les deux à la fois), plus souvent une offre d'achat (146) qu'une offre de vente (87), et tard : la moitié après 204 s.

Nos Hard recalés en retirent à peu près autant, 220 sur 60 manches simulées, mais toujours les deux côtés à la fois. Ils cotent aussi environ 1,5 fois plus (41 229 cotations). Je ne les ai pas changés : ils remplissent la table mixte de la règle d'entrée, ils sont réglés sur ces journaux, et les changer déplacerait toutes les mesures.

## Lire la couleur en fin de manche

Le consensus est une idée de Rasmus, déjà dans notre lecture du marché depuis la phase 5d : pour chaque couleur, le plus bas des plus hauts prix d'achat proposés par les autres joueurs. Pris seul, sans modèle, il désigne souvent mieux l'objectif que notre lecture complète :

| Couleur en tête | 180 s | 225 s | 239 s |
|---|---|---|---|
| vraies manches, notre lecture | 77 % | 85 % | 85 % |
| vraies manches, consensus brut | 85 % | 89 % | 91 % |
| manches simulées, notre lecture | 68 % | 71 % | 72 % |
| manches simulées, consensus brut | 62 % | 66 % | 67 % |

Les manches simulées sont 1 000 manches de la v4c « achat » contre des Hard recalés, à 4 ou 5 joueurs (graine 53).

Notre lecture n'a qu'une atténuation, 0,2, pour toute la manche. Mon hypothèse était qu'elle atténue trop les offres de fin de manche. J'ai écrit un prototype, hors du dépôt, avec une atténuation par fenêtre d'une minute. Il redonne exactement les chiffres d'aujourd'hui avec 0,2 partout. Le critère d'arrêt était fixé dans le plan : si la nouvelle lecture ne fait pas mieux sur les vraies manches à partir de 180 s, j'arrête là.

Choisies une fenêtre après l'autre, au meilleur log-score sur les 1 000 manches simulées de validation de la phase 5d, les atténuations sont 0,5 pour la première minute et 0,2 pour les trois autres. La fin de manche ne change pas. Sur les vraies manches, la lecture fait un peu moins bien :

| Vraies manches : probabilité de la vraie couleur, part en tête, perte log | 180 s | 225 s | 239 s |
|---|---|---|---|
| aujourd'hui (0,2 partout) | 0,63 ; 77 % ; 0,610 | 0,78 ; 85 % ; 0,406 | 0,81 ; 85 % ; 0,360 |
| par fenêtre (0,5 ; 0,2 ; 0,2 ; 0,2) | 0,62 ; 78 % ; 0,645 | 0,77 ; 82 % ; 0,436 | 0,80 ; 83 % ; 0,387 |

J'ai donc arrêté là, sans rien coder dans le dépôt.

La première table explique l'échec. Sur le site, le consensus trouve l'objectif à la cloche dans 91 % des manches. Entre nos Hard simulés, dans 67 % seulement. Les offres d'achat de nos Hard en disent beaucoup moins sur l'objectif que celles des vrais bots. Un réglage choisi en simulation ne peut pas apprendre à leur faire plus confiance, puisque, dans la simulation, elles ne le méritent pas.

## Le bot progresse-t-il ?

Non : cette phase ne change pas le bot. Elle explique pourquoi il laisse passer la carte qui départage une égalité, et elle montre un écart du simulateur qui touche tout ce que j'apprends en simulation. La v4c « achat » reste le bot de référence.

## Limites

Le gain du regroupement, au plus 6 $ par manche à 4 joueurs et 4 $ à 5, se calcule en connaissant la fin de la manche. Le vrai gain serait plus petit.

Les diagnostics opposent le bot à des Hard simulés seulement, et la dernière section montre que leurs offres diffèrent de celles du site.

Les 60 vraies manches viennent d'une seule table à 4 joueurs, contre le bot de Rasmus. Elles ne disent rien des tables à 5 joueurs.

Le prototype n'a essayé qu'une forme de changement, une atténuation par fenêtre, avec sept valeurs par fenêtre.

Tout reste mesuré contre des bots simulés ou sur le papier. Ces chiffres ne sont pas des gains réels sur figgie.com.

## Reproduire

```bash
cd projets/bot-figgie
python3 -m unittest                                                  # les 145 tests, environ 7 s
PYTHONPATH=. python3 resultats/phase5p/regroupement.py 200
PYTHONPATH=. python3 resultats/phase5p/valeur.py 100
PYTHONPATH=. python3 resultats/phase5p/croyances.py 100
PYTHONPATH=. python3 resultats/phase5p/retraits.py
PYTHONPATH=. python3 resultats/phase5p/mesure_lecture.py 1000
PYTHONPATH=. python3 resultats/phase5p/attenuation.py 1000
```

Les scripts et leurs sorties sont dans `resultats/phase5p/`. Sur 10 cœurs, chacun prend quelques minutes au plus. Pour revenir exactement au code de cette phase : `git checkout phase5p-figgie`.
