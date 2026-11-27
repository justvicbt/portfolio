# Phase 5s : réapprendre la lecture du site avec le Hard v3

*English version: [phase5s.en.md](phase5s.en.md)*

La lecture du site sert à toute la famille v4, et donc à la v4c « achat », le bot de référence. Elle s'appuie sur un modèle de signaux appris en phase 5d, sur des tables où jouaient les Hard simulés de la phase 5c. Or ces Hard proposaient des prix qui désignaient mal l'objectif (phase 5p). Depuis la phase 5r, le Hard v3 en est plus proche : ses offres d'achat désignent l'objectif presque aussi souvent que celles des bots du site. Dans cette phase, je réapprends ce modèle sur des tables où joue le Hard v3, sans rien changer d'autre.

Résultat : sur les 60 vraies manches de Rasmus, qui ne servent jamais à apprendre, la nouvelle lecture trouve l'objectif à la cloche dans 98 % des manches, contre 85 %. La v4c « achat » avec cette lecture, `v4c_achat_v3`, passe la règle d'entrée au tournoi réduit et au tournoi complet, à 4 et à 5 joueurs. Elle gagne environ 10,5 $ par manche de plus que la v4c « achat » quand les deux jouent à la même table. Elle devient le bot de référence. Elle gagne en revanche moins que l'ancienne face aux Hard simulés des phases 5c et 5j. Les gains de tournoi sont mesurés contre des bots simulés, pas sur le site.

## D'où viennent les 35 $ contre le Hard v3

En phase 5r, la v4c « achat » battait trois Hard v3 de 35 $ par manche, deux fois plus que trois Hard recalés. Avant d'apprendre quoi que ce soit sur ces tables, je voulais savoir si ce gain venait d'un défaut du Hard v3. La règle d'arrêt était fixée dans le plan : s'il bradait par exemple l'objectif en début de manche, je m'arrêtais là.

Le gain d'un joueur se découpe exactement en trois parts :
- la donne : 10 $ par carte objectif reçue, moins la mise ;
- les échanges, chaque carte comptée à sa valeur de fin, 10 $ pour l'objectif et 0 pour les autres : acheter l'objectif à 7 $ rapporte 3 $, vendre une autre couleur à 4 $ rapporte 4 $ ;
- la prime de majorité, la part du reste du pot.

J'ai joué les mêmes 500 parties de 10 manches (règle du site, la v4c « achat » au siège 0) contre trois Hard recalés puis contre trois Hard v3. Le script vérifie à chaque manche que les trois parts redonnent le gain exact.

| Par manche, v4c « achat » | contre Hard recalés | contre Hard v3 | écart |
|---|---|---|---|
| gain total | 18,07 $ | 35,99 $ | +17,92 $ |
| donne | -26,41 $ | -26,41 $ | 0 |
| prime de majorité | 45,91 $ | 57,14 $ | +11,23 $ |
| achats et ventes de l'objectif | -4,86 $ | -1,51 $ | +3,35 $ |
| ventes des autres couleurs | 13,30 $ | 16,09 $ | +2,79 $ |
| achats des autres couleurs | -9,87 $ | -9,32 $ | +0,55 $ |
| cartes objectif achetées / vendues | 0,90 / 0,78 | 1,15 / 0,53 | |
| seule en tête de l'objectif en fin de manche | 36 % | 48 % | |

Sur ces 500 parties, l'écart est de 18 $ et non de 17 comme au tournoi : les donnes et les places à table ne sont pas les mêmes.

L'essentiel, environ 14,6 $, vient de l'objectif. Contre le Hard v3, la v4c « achat » achète plus de cartes objectif, en vend moins, et finit plus souvent seule en tête. Le Hard v3 ne brade pas l'objectif : ce qu'elle gagne en l'achetant en première minute passe de 0,26 à 0,91 $ seulement. Elle lit mieux l'objectif parce que les offres d'achat du Hard v3 le désignent, ce qui arrive aussi sur le site. Environ 2,8 $ viennent des cartes hors objectif qu'elle lui vend plus cher, surtout en dernière minute (+2,27 $). C'est le défaut déjà noté en phase 5r : le Hard v3 prend trop d'offres hors objectif à 4-6 $. Il gonfle un peu les gains contre le Hard v3 sans les expliquer, et la règle d'arrêt ne s'appliquait pas.

## Le modèle réappris

`figgie.learn --site` reçoit l'option `--hard`, qui choisit le Hard simulé des tables d'apprentissage. Tout le reste ne change pas : les mêmes tables à 4 ou 5 joueurs, le même voisin à la même place, les mêmes graines (51 pour apprendre, 52 pour valider), 2 400 manches d'apprentissage et 600 de validation. Le nouveau modèle va dans `modeles/signaux_site_v3.json`. L'ancien n'est pas touché, et aucun bot existant ne change.

Un seul seam, écrit en TDD : une nouvelle fonction `site_table` donne la graine et les joueurs de chaque table. Le test vérifie qu'avec le Hard v3, la table est la même qu'avant, Hard remplacé. Il échouait avant le code. Il attrape deux erreurs volontaires : ignorer le Hard demandé, et changer les tirages des tables quand on change de Hard.

L'apprentissage prend 32 s sur 10 cœurs. Sur les manches de validation simulées, l'atténuation retenue est 0,5, et la lecture y trouve l'objectif à 240 s dans 97,5 % des manches. La sortie complète est dans `resultats/phase5s/apprentissage.txt`.

## Le critère sur les vraies manches

Je l'avais fixé avant l'apprentissage. Sur les 60 vraies manches, à 180, 225 et 239 s, la nouvelle lecture doit avoir une perte log plus basse que l'actuelle, et une part de manches où la vraie couleur est en tête au moins égale. `figgie.reel --calibration` reçoit l'option `--signals` pour mesurer un autre modèle ; avec l'ancien, elle redonne exactement les chiffres des phases précédentes.

| Vraies manches : probabilité de la vraie couleur ; part en tête ; perte log | 60 s | 120 s | 180 s | 225 s | 239 s |
|---|---|---|---|---|---|
| modèle de la phase 5d | 0,31 ; 43 % ; 1,281 | 0,41 ; 53 % ; 1,031 | 0,63 ; 77 % ; 0,610 | 0,78 ; 85 % ; 0,406 | 0,81 ; 85 % ; 0,360 |
| modèle appris avec le Hard v3 | 0,31 ; 43 % ; 1,295 | 0,52 ; 62 % ; 0,999 | **0,90 ; 95 % ; 0,188** | **0,95 ; 95 % ; 0,146** | **0,98 ; 98 % ; 0,098** |

Le critère est largement rempli. À la cloche, le consensus brut des offres d'achat trouvait l'objectif dans 91 % des vraies manches (phase 5p). La nouvelle lecture fait mieux que lui, en ajoutant le comptage des cartes et la confiance par joueur. En phase 5p, une lecture réglée en simulation faisait moins bien sur les vraies manches ; cette fois, ce que le bot apprend en simulation se vérifie sur des données réelles. À 60 s, rien ne change, ce que le critère ne regardait pas.

## Le tournoi réduit

Le candidat `v4c_achat_v3` est la v4c « achat » avec ce seul changement : le nouveau modèle de signaux et son atténuation. Ses réglages restent ceux de la v4c. Il a joué le tournoi réduit de la phase 5r (10 manches, 100 donnes, règle du site, Hard v3 à la table mixte), avec en plus la v4c « achat » parmi les références. Il passe la règle d'entrée aux deux tailles et bat la v4c « achat » à la même table : -10,70 $ [-11,77 ; -9,63] à 4 joueurs, -11,39 $ [-12,44 ; -10,34] à 5 (écart référence moins candidat). Le tournoi a pris 2 h 50.

## Le tournoi complet

Comme en phase 5n : graine 1, 300 donnes de 10 manches, règle du site, et toutes les références de la 5n à la table mixte, plus la v4c « achat ». Le Hard v3 remplit la table mixte. Le tournoi a pris 12 h 50 sur 10 cœurs.

La règle d'entrée passe à 4 et à 5 joueurs : les 21 références ont toutes leur intervalle entier sous 0. Les plus proches, en écart référence moins candidat, en dollars par manche :

| Référence | 4 j. | 5 j. |
|---|---|---|
| v4c « achat » (référence jusqu'ici) | -10,33 [-10,93 ; -9,74] | -10,96 [-11,52 ; -10,40] |
| v4c qui se tait | -13,25 [-13,93 ; -12,58] | -12,67 [-13,25 ; -12,09] |
| v4c vendeuse | -13,54 [-14,23 ; -12,86] | -13,90 [-14,44 ; -13,37] |
| v4c au temps | -14,47 [-15,08 ; -13,86] | -13,81 [-14,34 ; -13,29] |
| v4c | -16,35 [-17,13 ; -15,57] | -13,45 [-14,17 ; -12,73] |
| v4b | -18,39 [-19,20 ; -17,57] | -11,02 [-11,75 ; -10,29] |
| exploiteur lecteur | -47,13 [-48,19 ; -46,08] | -37,60 [-38,50 ; -36,70] |

Contre trois copies d'un même adversaire, comparé à la v4c « achat » au tournoi complet de la phase 5n, sur les mêmes donnes :

| Adversaire | v4c_achat_v3, 4 j. | v4c « achat », 4 j. | v4c_achat_v3, 5 j. | v4c « achat », 5 j. |
|---|---|---|---|---|
| Hard v3 | +54,52 [+53,66 ; +55,38] | | +50,41 [+49,68 ; +51,13] | |
| bayésien | +32,18 | +25,73 | +33,87 | +25,45 |
| marginal | +13,43 | +13,00 | +10,03 | +9,16 |
| heuristique | +41,26 | +41,39 | +38,51 | +39,23 |
| sniper | +32,24 | +32,24 | +30,05 | +30,05 |
| Hard recalé (5j) | +13,83 [+12,81 ; +14,86] | +17,83 [+16,91 ; +18,75] | +11,80 [+10,94 ; +12,66] | +16,55 [+15,75 ; +17,34] |
| Hard de la phase 5c | +33,78 | +41,71 | +32,39 | +38,00 |

La v4c « achat » n'avait pas joué le Hard v3 en 5n ; au tournoi réduit de la 5r, elle le battait de 34,76 $ à 4 joueurs et de 33,38 $ à 5. Tous les chiffres sont dans `resultats/phase5s/tournoi_complet.md`.

## Le bot progresse-t-il ?

Oui, au sens de la règle d'entrée et sur les vraies manches. `v4c_achat_v3` passe la règle d'entrée aux deux tailles, au tournoi réduit comme au tournoi complet. Face à la v4c « achat », à la même table, elle gagne 10,33 $ par manche à 4 joueurs et 10,96 $ à 5. C'est le plus gros écart d'une promotion depuis que la règle se joue à la table mixte. Sa lecture de l'objectif progresse aussi sur les vraies manches, la seule mesure de cette phase qui ne dépend pas du simulateur. Je la promeus donc : elle devient le bot de référence, à la place de la v4c « achat ».

Elle a un prix. Face aux Hard simulés des phases 5c et 5j, elle gagne 4 à 8 $ de moins par manche que la v4c « achat ». Sa lecture fait plus confiance aux offres d'achat, ce qui paie quand elles désignent l'objectif et coûte quand elles ne le désignent pas. La promotion parie donc que le site ressemble au Hard v3 plus qu'aux anciens. Les vraies manches vont dans ce sens.

## Limites

Le gain à la table mixte est mesuré avec le Hard v3, et c'est avec lui que la lecture a été apprise. Le tournoi favorise donc un bot qui a appris sur ce même Hard. La vérification sur les vraies manches porte sur la lecture de l'objectif, pas sur les gains.

Le Hard v3 paie trop cher les cartes hors objectif. Une part, environ 2,8 $ par manche, de ce que la v4c « achat » lui prend vient de là, et `v4c_achat_v3` en profite sans doute aussi.

Le Hard v3 et la nouvelle lecture viennent tous deux d'une seule table à 4 joueurs, contre le bot de Rasmus, sur 60 manches. Rien ne dit que le site se comporte de la même façon à 5 joueurs.

Les réglages de la v4c ont été réappris en phase 5m avec l'ancienne lecture. Je ne les ai pas réappris avec la nouvelle.

Tout reste mesuré sur le papier ou contre des bots simulés. Ces chiffres ne sont pas des gains réels sur figgie.com.

## Reproduire

```bash
cd projets/bot-figgie
python3 -m unittest                                                  # les 149 tests, environ 7 s
PYTHONPATH=. python3 resultats/phase5s/gain_v3.py 500
python3 -m figgie.learn --site --hard hard_simule_v3 --train 2400 --valid 600 --out modeles/signaux_site_v3.json --report resultats/phase5s/signaux_site_v3.json
PYTHONPATH=. python3 resultats/phase5s/mesure_reelle.py
python3 -m figgie.tournoi --site --candidates v4c_achat_v3 --rounds 10 --deals 100 --no-tables --filler hard_simule_v3 \
  --opponents heuristique sniper bayesien marginal hard_simule hard_simule_v2 hard_simule_v3 --references \
  --mixed v4c_achat hard_simule_v2 bayesien marginal adaptatif_v3 adaptatif_v4b adaptatif_v4c v4c_calme_60 v4c_vente_60 \
          exploiteur exploiteur_lecteur vendeur parieur v4c_temps \
  --out resultats/phase5s/tournoi_reduit.json
python3 -m figgie.tournoi --site --candidates v4c_achat_v3 --rounds 10 --deals 300 --no-tables --filler hard_simule_v3 \
  --opponents heuristique sniper bayesien marginal hard_simule hard_simule_v2 hard_simule_v3 --references \
  --mixed v4c_achat hard_simule heuristique sniper bayesien marginal adaptatif_v3 adaptatif_v4b exploiteur \
          exploiteur_lecteur imitateur fondamentaliste fondamentaliste_35 vendeur mante parieur hard_simule_v2 \
          adaptatif_v4c v4c_calme_60 v4c_vente_60 v4c_temps \
  --out resultats/phase5s/tournoi_complet.json
```

Sur 10 cœurs, le diagnostic prend 3 min, l'apprentissage 32 s, le tournoi réduit 2 h 50 et le tournoi complet 12 h 50. Les sorties sont dans `resultats/phase5s/`. Pour revenir exactement au code de cette phase : `git checkout phase5s-figgie`.
