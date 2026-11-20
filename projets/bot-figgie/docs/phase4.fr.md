# Phase 4 : ligue et robustesse

*English version: [phase4.en.md](phase4.en.md)*

Les phases précédentes mesuraient toujours un candidat seul face à des copies d'un adversaire. La phase 3 a montré que ce n'est pas suffisant : quand les lecteurs sont nombreux à la table, un adversaire seul les exploite. Cette phase cherche systématiquement ce genre de faiblesse. Elle ajoute un test de minorité à la règle d'entrée, fait chercher par la machine les adversaires qui battent le mieux nos bots, réentraîne le lecteur sur des parties où il joue contre lui-même et contre ces adversaires, puis le confronte à des comportements anormaux : un joueur inactif, un spammeur, des menteurs.

Le bilan est net, et il est négatif. Aucun candidat ne passe la règle d'entrée complète à 4 et à 5 joueurs. Même le bot de référence, le marginal, se fait exploiter quand il est en minorité. Les réglages ne permettent pas d'en sortir : quand on resserre le spread, le bot se fait exploiter, et quand on l'élargit, il perd contre les autres. C'est la leçon principale de la phase. Avec des réglages fixes, il n'existe sans doute pas de bot qu'on ne puisse pas exploiter, parce que la bonne stratégie dépend de ce que font les autres.

## Un moteur plus rapide, sans rien changer

Le tournoi de la phase 3 prenait près de deux heures. Avant d'en lancer d'autres, j'ai profilé le moteur. Le goulot n'était pas le moteur lui-même : la moitié du temps passait dans le calcul du gain d'une carte, appelé plus d'un million de fois pour 8 manches, alors que les mêmes situations reviennent sans cesse. Le programme garde maintenant chaque résultat déjà calculé. Les manches les plus lentes passent de 49 à 30 millisecondes, les autres de 23 à 16.

Pour vérifier que rien n'a changé, j'ai d'abord enregistré, avec le moteur de la phase 3, les gains et l'empreinte complète du journal de plusieurs manches et d'une partie de trois manches. Un test, dit « de référence », rejoue ces manches et exige les mêmes valeurs, au centime près. Il vérifie aussi que le modèle appris n'a pas changé, pour qu'un échec désigne bien le moteur et pas un modèle réappris entre-temps.

## Le test de minorité

La règle d'entrée demandait de battre nettement chaque référence : un intervalle de confiance entièrement au-dessus de zéro, en jouant seul face à trois ou quatre copies d'elle. Elle exige désormais aussi l'inverse : chaque référence, seule face à des copies du candidat, ne doit pas gagner nettement. Un bot qui se fait exploiter quand il est nombreux à la table est refusé, même s'il gagne en tête-à-tête.

## Des exploiteurs trouvés par la machine

Pour trouver les faiblesses de nos bots, j'ai fait chercher automatiquement l'adversaire qui leur prend le plus. Un exploiteur est un bot de la mécanique commune, défini par six réglages :

- d'où viennent ses valeurs (heuristique, bayésienne ou marginale) ;
- son spread et sa marge de prise ;
- sa vitesse de réaction ;
- s'il cote ou se contente de prendre ;
- son rythme.

La recherche se fait en trois étapes, chacune sur ses propres donnes, pour ne pas retenir un réglage simplement chanceux. On essaie d'abord 60 réglages tirés au hasard, sur 60 donnes (graine 5). On remesure les 6 meilleurs sur 300 autres donnes (graine 6). On mesure enfin le gagnant sur les 1 000 donnes des tournois (graine 1), qu'aucune étape précédente n'a vues. Chaque mesure est faite avec l'exploiteur seul face à des copies du bot visé.

| Bot visé | 4 joueurs | 5 joueurs |
|---|---|---|
| marginal | +4,35 $ [+3,54 ; +5,15] | +7,22 $ [+6,56 ; +7,88] |
| lecteur | +2,78 $ [+1,88 ; +3,69] | +8,50 $ [+6,89 ; +10,11] |

Gain de l'exploiteur par manche. Les deux meilleurs bots sont exploitables.

Trois des quatre recherches ont trouvé le même exploiteur : des valeurs bayésiennes, un spread de 6 $, une marge de 3 $ et une réaction en 0,3 seconde. Il cote plus près de sa valeur que le marginal, qui cote à 8 $, donc ses prix sont les meilleurs du carnet et c'est lui qu'on vient chercher. Mais il est plus exigeant pour prendre une cotation (3 $ d'avantage minimum au lieu de 1 $). Face à trois marginaux, il devient le teneur de marché de la table. Contre le lecteur à 5 joueurs, le meilleur exploiteur utilise des valeurs marginales, un spread de 4 $, une marge de 3 $ et une action au plus toutes les 2 secondes.

Ces deux exploiteurs rejoignent le zoo. C'est la ligue : ils servent à la fois d'adversaires dans la règle d'entrée et de joueurs dans les parties d'apprentissage. Seuls face à des copies, ils gagnent. À l'inverse, face à des copies d'eux, le marginal les bat largement (+19,9 $ et +12,8 $ à 4 joueurs).

## La ligue : réapprendre le lecteur

Le lecteur de la phase 3 avait appris sur des tables où personne ne lisait le marché. J'ai réappris son modèle de signaux sur 4 000 manches de la ligue, avec de nouvelles graines (7 pour l'apprentissage, 8 pour la validation). Ces tables étaient tirées dans tout le zoo, lecteurs, exploiteurs et menteurs compris. Le nouveau modèle trouve la couleur objectif dans 51,5 % des cas à une minute, autant que celui de la phase 3, mais sur des tables bien plus variées. Ses probabilités restent bien calibrées.

J'ai ensuite réglé le spread et la marge de ce « lecteur ligue » à 5 joueurs, là où le lecteur échouait. J'ai pris en compte le test de minorité face aux 10 adversaires du zoo, 12 combinaisons au départ puis deux spreads plus larges. Avec une marge de 3 $, la meilleure :

| Spread | Contre le marginal | Marginal seul face aux lecteurs | Aléatoire seul face aux lecteurs | Pire borne basse |
|---|---|---|---|---|
| 3 $ | -1,1 | +43,2 | +44,2 | -52,5 |
| 4 $ | +0,8 | +34,5 | +26,6 | -40,2 |
| 6 $ | +2,8 | +21,1 | -4,7 | -25,9 |
| 8 $ | +0,8 | +9,0 | -34,9 | -12,6 |
| 10 $ | -2,9 | +5,9 | -55,5 | -9,0 |
| 12 $ | -5,5 | +5,2 | -68,8 | -10,2 |

Gains en dollars par manche, à 5 joueurs, sur les donnes d'entraînement (graine 2, 150 donnes). Les colonnes « seul » donnent le gain de l'adversaire seul face à quatre lecteurs : plus il est haut, plus les lecteurs se font exploiter.

Le tableau montre le dilemme. Avec un spread serré, quatre lecteurs se disputent les mêmes clients en se faisant concurrence sur les prix, et même un joueur aléatoire seul leur prend 44 $ par manche. Avec un spread large, l'exploitation recule, mais le lecteur perd alors contre le marginal. Aucun réglage ne gagne des deux côtés. Le critère fixé à l'avance, le meilleur pire cas, retient un spread de 10 $.

## Comportements anormaux

Trois bots anormaux, hors du zoo :

- l'inactif ne fait jamais rien, comme un joueur déconnecté ;
- le spammeur envoie des cotations au hasard aussi vite que possible ;
- le menteur joue comme le marginal, mais affiche toutes les 6 secondes une offre d'achat à 12 $ dans la couleur qu'il juge la moins utile, et la retire 1,5 seconde plus tard. Il vise les bots qui lisent le marché.

Le spammeur a obligé à ajouter une limite au moteur, comme sur un vrai site : 0,05 seconde au minimum entre deux actions d'un même joueur, soit 20 actions par seconde au plus. Aucun bot existant n'est aussi rapide, et le test de référence l'a confirmé. La relecture du code a signalé deux défauts dans le menteur. Le premier était réel : sa fausse offre pouvait être refusée parce qu'elle croisait sa propre offre de vente, et il ne mentait alors plus pendant 6 secondes. Il est corrigé. Le second ne l'était qu'à moitié : en retirant sa fausse offre, il retire aussi sa vraie vente dans cette couleur, mais il la reposte dès que le mensonge est fini. Un test vérifie les deux.

| Table (4 joueurs, 300 donnes) | marginal | lecteur | lecteur ligue |
|---|---|---|---|
| inactif, heuristique, marginal | +21,7 | +20,7 | +15,3 |
| spammeur, heuristique, marginal | +122,8 | +109,6 | +99,1 |
| menteur, menteur, heuristique | +19,1 | +16,1 | +18,3 |
| les mêmes, parties de 10 manches | +19,4 | +16,8 | +19,7 |

Les trois candidats gagnent nettement à toutes ces tables. Le spammeur se fait littéralement vider par tout le monde.

Le menteur ne trompe guère le lecteur, et ce n'est pas grâce à la mémoire. Sur 200 parties de 10 manches, le lecteur qui se souvient de ses adversaires fait en moyenne -0,75 $ par manche de moins que celui qui oublie, avec un intervalle [-1,82 ; +0,32] qui contient zéro. En fin de partie, il n'accorde aux menteurs qu'une confiance de 0,84, contre 0,95 à l'heuristique. L'explication est sans doute le dédoublonnage de la phase 3 : chaque signal ne compte qu'une fois par joueur, couleur et tranche de prix. Un menteur qui répète son mensonge toutes les 6 secondes ne pèse donc pas plus qu'un seul mensonge, et le reste de ses cotations, celles d'un marginal, est utile.

## Résultats

Les trois candidats ont été mesurés face aux 10 adversaires du zoo, avec le test de minorité face aux 4 références, sur 1 000 donnes dupliquées (graine 1). Le tournoi a pris 1 h 12 sur 10 cœurs.

| Candidat | 4 joueurs, sans minorité | 4 joueurs, avec | 5 joueurs, sans minorité | 5 joueurs, avec |
|---|---|---|---|---|
| marginal | accepté | refusé : bayésien seul +1,35 [+0,34 ; +2,36] | accepté | accepté |
| lecteur | accepté | accepté | refusé : contre le marginal +0,7 [-0,3 ; +1,7] | refusé : marginal seul +7,35 [+6,0 ; +8,7] |
| lecteur ligue | accepté | accepté | refusé : contre le marginal -1,34 [-2,24 ; -0,43] | refusé : marginal seul +4,67 [+3,4 ; +5,9] |

Quelques lignes de plus, en dollars par manche :

| | marginal | lecteur | lecteur ligue |
|---|---|---|---|
| contre l'exploiteur, 4 j. | +19,9 | +26,5 | +27,2 |
| contre l'exploiteur du lecteur, 5 j. | +9,5 | +8,0 | +7,9 |
| contre le passif, 4 j. | +15,2 | +19,8 | +21,3 |
| lecteur ligue contre lecteur | | | -1,6 (4 j.), -1,9 (5 j.) |

Aucun candidat ne passe la règle d'entrée complète. Aucun n'est donc promu, et le marginal reste le bot de référence, en sachant désormais qu'il n'est pas inexploitable. À 4 joueurs, un bayésien seul face à trois marginaux gagne +1,35 $ par manche, et l'exploiteur trouvé par la machine +4,35 $. Le lecteur ligue ne fait pas mieux que le lecteur : il perd même un peu contre lui, à 4 comme à 5 joueurs. Réapprendre sur la ligue et régler pour la minorité n'a pas réglé le problème.

## Ce que j'en retiens

Un bot à réglages fixes est une cible. Chaque réglage a sa contre-stratégie, et la machine la trouve en quelques minutes. Contre des marginaux qui cotent à 8 $ de leur valeur, il suffit de coter à 6 $ pour prendre tout le flux. Contre des lecteurs serrés, même un joueur aléatoire gagne. En théorie des jeux, un bot qu'aucun adversaire seul ne pourrait exploiter serait un équilibre de Nash symétrique. Ça existe, mais rien ne garantit qu'on le trouve en choisissant deux nombres une fois pour toutes.

Les copies se font concurrence. Quatre bots identiques veulent les mêmes cartes, au même prix, et se battent pour la même majorité. Un joueur différent profite de cette guerre des prix. Pour l'éviter, un bot devrait remarquer qu'il a des concurrents qui lui ressemblent et ajuster son jeu en cours de partie, par exemple en cotant moins serré quand d'autres cotent déjà au même prix.

C'est l'argument le plus fort pour la suite du projet. Un bot qui ajuste ses réglages en cours de partie, à la table qu'il a en face, n'est plus une cible fixe. C'est aussi ce que demandait le projet dès le départ : un bot qui apprend à chaque partie. La mémoire de la phase 3 apprenait à qui se fier, et ça ne rapportait rien. Apprendre comment jouer face à cette table-là devrait rapporter davantage, et le test de minorité dira si c'est le cas.

Chercher activement les faiblesses vaut mieux que les attendre. Le zoo de départ avait été écrit à la main, et le marginal le battait entièrement. Une recherche de 20 minutes a suffi à trouver deux adversaires qui le battent en minorité.

## Limites

Tous les adversaires restent des bots, qu'ils aient été écrits à la main ou trouvés par la recherche. La recherche d'exploiteurs n'explore que la famille de la mécanique commune, avec six réglages. Des adversaires d'une autre famille trouveraient peut-être d'autres faiblesses.

Le test de minorité n'utilise que les quatre références (heuristique, sniper, bayésien, marginal). Les exploiteurs n'en font pas partie, alors que ce sont eux qui exploitent le mieux. Avec eux, le marginal serait aussi refusé à 5 joueurs.

Les réglages ont été choisis sur 150 donnes d'entraînement par adversaire, ce qui laisse des intervalles de quelques dollars. Le choix entre deux réglages voisins reste fragile.

Les limites des phases précédentes tiennent toujours : temps de réaction inventés, quatre règles du site supposées, argent qui repart de 350 $ à chaque manche.

## Reproduire

```bash
cd projets/bot-figgie
python3 -m unittest                                              # les 87 tests, environ 2 s
python3 -m figgie.exploit --target marginal --players 4          # recherche d'un exploiteur, environ 5 min
python3 -m figgie.learn --train 4000 --valid 1000 --league       # modèle de la ligue, environ 40 s
python3 -m figgie.tune --bot lecteur_ligue --players 5 --minority --spreads 3 4 6 8 --edges 1 2 3
python3 -m figgie.memoire --deals 200 --rounds 10 --table menteur,menteur,heuristique
python3 -m figgie.tournoi --candidates marginal lecteur lecteur_ligue --out tournoi.json   # environ 1 h 15
```

Pour revenir exactement au code de cette phase : `git checkout phase4-figgie`.

## Et ensuite

La suite logique est un bot qui adapte son jeu en cours de partie. Il garderait le calcul de valeur du marginal et la lecture du marché, mais choisirait son spread et sa marge manche après manche, selon ce qui rapporte face à la table qu'il a en face. C'est un problème de bandit : essayer, mesurer, privilégier ce qui marche sans cesser d'explorer. Il sera mesuré avec la même règle d'entrée, test de minorité compris, et face aux exploiteurs de cette phase.
