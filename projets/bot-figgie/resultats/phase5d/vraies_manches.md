60 vraies manches (journaux de Rasmus Suonio, son bot contre 3 bots Hard de figgie.com)

Rejeu sur le papier, notre bot à la place de celui de Rasmus : score moyen par manche [IC 95 %]
(argent des prises + 10 $ par carte objectif de plus ; la majorité n'est pas comptée, toutes les prises sont servies)
  lecteur           -26.88 [-34.02 ; -19.75]   prises par manche 19.9
  lecteur_site      -15.72 [-23.22 ; -8.21]   prises par manche 19.2
  adaptatif_v4       -4.57 [-10.65 ; +1.51]   prises par manche 13.2
  adaptatif_v3      -18.83 [-27.28 ; -10.39]   prises par manche 20.5
  bayesien           +8.97 [+0.43 ; +17.50]   prises par manche 23.5
  marginal          -26.37 [-35.33 ; -17.41]   prises par manche 23.1

Probabilité de la vraie couleur objectif, vue du siège de Rasmus : P moyenne / part des manches où elle est la plus probable / perte log
  donne     t=  0 s : 0.30 / 45% / 1.28   t= 60 s : 0.30 / 45% / 1.28   t=120 s : 0.30 / 45% / 1.28   t=180 s : 0.30 / 45% / 1.28   t=239 s : 0.30 / 45% / 1.28
  comptage  t=  0 s : 0.30 / 45% / 1.28   t= 60 s : 0.30 / 45% / 1.28   t=120 s : 0.31 / 47% / 1.26   t=180 s : 0.31 / 47% / 1.26   t=239 s : 0.31 / 45% / 1.25
  lecture   t=  0 s : 0.30 / 45% / 1.28   t= 60 s : 0.29 / 33% / 1.43   t=120 s : 0.39 / 45% / 1.14   t=180 s : 0.54 / 68% / 0.76   t=239 s : 0.71 / 88% / 0.45
  lecture site t=  0 s : 0.30 / 45% / 1.28   t= 60 s : 0.31 / 43% / 1.28   t=120 s : 0.41 / 53% / 1.03   t=180 s : 0.63 / 77% / 0.61   t=239 s : 0.81 / 85% / 0.36

Écarts appariés manche par manche (mêmes 60 manches, score de A moins score de B) [IC 95 %]
  adaptatif_v4 - adaptatif_v3   +14.27 [+6.16 ; +22.37]
  lecteur_site - lecteur        +11.17 [+4.56 ; +17.78]
  adaptatif_v4 - lecteur_site   +11.15 [+5.21 ; +17.09]
  adaptatif_v4 - marginal       +21.80 [+13.11 ; +30.49]
  adaptatif_v4 - bayesien       -13.53 [-23.21 ; -3.86]
