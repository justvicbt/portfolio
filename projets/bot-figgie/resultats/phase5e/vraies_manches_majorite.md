60 vraies manches (journaux de Rasmus Suonio, son bot contre 3 bots Hard de figgie.com)

Rejeu sur le papier, notre bot à la place de celui de Rasmus : score moyen par manche [IC 95 %]
(argent des prises + 10 $ par carte objectif de plus ; majorité estimée sur des mains possibles des autres, toutes les prises sont servies)
  bayesien          -55.20 [-70.68 ; -39.72]   prises par manche 23.5
  adaptatif_v4      -18.72 [-31.15 ; -6.28]   prises par manche 13.2
  adaptatif_v3      -43.35 [-57.79 ; -28.91]   prises par manche 20.5
  lecteur_site      -32.49 [-47.18 ; -17.79]   prises par manche 19.2
  lecteur           -50.26 [-65.47 ; -35.05]   prises par manche 19.9
  marginal          -48.67 [-65.23 ; -32.10]   prises par manche 23.1
  sniper            -55.20 [-70.68 ; -39.72]   prises par manche 23.5
  hard_simule       -70.54 [-85.55 ; -55.53]   prises par manche 17.4
  heuristique       -94.49 [-115.90 ; -73.08]   prises par manche 23.4
  exploiteur        -41.20 [-55.96 ; -26.44]   prises par manche 10.3

Part de la majorité estimée dans le score (avec moins sans), par manche
  bayesien -64.17   exploiteur -58.47   adaptatif_v3 -24.52   marginal -22.30   lecteur_site -16.77   adaptatif_v4 -14.15

Écarts appariés manche par manche [IC 95 %], sans et avec la majorité estimée
  adaptatif_v4 - bayesien       sans -13.53 [-23.21 ; -3.86]   avec +36.48 [+19.23 ; +53.73]
  adaptatif_v4 - adaptatif_v3   sans +14.27 [+6.16 ; +22.37]   avec +24.63 [+9.81 ; +39.45]
  adaptatif_v4 - lecteur_site   sans +11.15 [+5.21 ; +17.09]   avec +13.77 [+3.39 ; +24.14]
  lecteur_site - marginal       sans +10.65 [+4.14 ; +17.16]   avec +16.18 [+3.44 ; +28.92]
  adaptatif_v4 - exploiteur     sans -21.83 [-29.15 ; -14.52]   avec +22.48 [+5.95 ; +39.02]
  adaptatif_v3 - bayesien       sans -27.80 [-38.47 ; -17.13]   avec +11.85 [-4.02 ; +27.72]
  adaptatif_v4b  sans   -3.78 [-9.26 ; +1.70]  avec  -16.09 [-29.07 ; -3.11]  prises 13.5
  adaptatif_v4   sans   -4.57 [-10.65 ; +1.51]  avec  -18.72 [-31.15 ; -6.28]  prises 13.2
  v4b - v4 (sans majorité) +0.78 [-1.81 ; +3.38]
  v4b - v4 (avec majorité) +2.63 [-1.94 ; +7.20]
