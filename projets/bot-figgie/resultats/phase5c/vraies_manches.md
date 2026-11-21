60 vraies manches (journaux de Rasmus Suonio, son bot contre 3 bots Hard de figgie.com)

Mesures du marché (bots Hard seulement) :
  rounds                 60
  trades                 53.266666666666666
  hard_trades_per_pair   9.43888888888889
  by_minute              [0.11712772218952325, 0.1883460859329017, 0.25250147145379637, 0.4420247204237787]
  quotes_per_min         37.75
  first_quote            5.0
  goal_price             7.0
  other_price            3
  goal_top_bid           10.0
  other_top_bid          5.0

Rejeu sur le papier, notre bot à la place de celui de Rasmus : score moyen par manche [IC 95 %]
(argent des prises + 10 $ par carte objectif de plus ; la majorité n'est pas comptée, toutes les prises sont servies)
  marginal          -26.37 [-35.33 ; -17.41]   prises par manche 23.1
  adaptatif_v3      -18.83 [-27.28 ; -10.39]   prises par manche 20.5
  lecteur           -26.88 [-34.02 ; -19.75]   prises par manche 19.9
  bayesien           +8.97 [+0.43 ; +17.50]   prises par manche 23.5
  heuristique       -41.83 [-56.72 ; -26.95]   prises par manche 23.4
  hard_simule       -37.15 [-45.51 ; -28.79]   prises par manche 17.4

Probabilité de la vraie couleur objectif, vue du siège de Rasmus : P moyenne / part des manches où elle est la plus probable / perte log
  donne     t=  0 s : 0.30 / 45% / 1.28   t= 60 s : 0.30 / 45% / 1.28   t=120 s : 0.30 / 45% / 1.28   t=180 s : 0.30 / 45% / 1.28   t=239 s : 0.30 / 45% / 1.28
  comptage  t=  0 s : 0.30 / 45% / 1.28   t= 60 s : 0.30 / 45% / 1.28   t=120 s : 0.31 / 47% / 1.26   t=180 s : 0.31 / 47% / 1.26   t=239 s : 0.31 / 45% / 1.25
  lecture   t=  0 s : 0.30 / 45% / 1.28   t= 60 s : 0.29 / 33% / 1.43   t=120 s : 0.39 / 45% / 1.14   t=180 s : 0.54 / 68% / 0.76   t=239 s : 0.71 / 88% / 0.45
