# Salut, moi c'est Victor

Je travaille en conformité et en gestion des risques depuis 2021 (banque d'investissement, immobilier, gestion de patrimoine). Au fil des missions, j'ai eu de plus en plus envie de comprendre ce qui se passe sous le capot : les données, les modèles, le code. Aujourd'hui je me forme à la data et à l'IA appliquées à la finance (MSc Data Management, IA & Stratégie Financière à l'INSEEC).

Ce repo, c'est mon carnet de projets. J'y mets ce que je construis pour apprendre, tester une idée ou répondre à un vrai besoin. Certains sont aboutis, d'autres sont des brouillons assumés. Chaque projet a son propre dossier avec un README qui explique le pourquoi, le comment et ce que j'en ai retenu.

Je l'enrichis au fur et à mesure, donc repassez de temps en temps.

## Les projets

| Projet | En deux mots | Domaine | Stack | Statut |
|---|---|---|---|---|
| [Moteur de stratégie F1](./projets/moteur-strategie-f1) | Données réelles de 4 Grands Prix 2025 : base SQL, modèle de dégradation des pneus et simulateur 1 contre 2 arrêts | Data | Python, SQL (SQLite), pandas, statsmodels | Terminé (v1) |
| [Risque d'undercut F1](./projets/risque-undercut-f1) | Monte Carlo sur la saison 2025 : probabilité de réussite, gain et pire cas d'un undercut, avec safety cars, arrêts et trafic, confronté aux vraies tentatives | Risque | Python, numpy, pandas, statsmodels, SQLite | Terminé (v1) |
| [Centre de commande F1](./projets/centre-commande-f1) | Tableau de bord qui rejoue 4 Grands Prix 2025 (pipeline ETL météo et tours, écarts au tour, pneus, stratégie), chaque enseignement avec son incertitude | Data | Python, Streamlit, Plotly, pandas, SQLite | Terminé (v1) |
| [Carte de vitesse F1](./projets/carte-vitesse-f1) | Le tracé d'un circuit coloré selon la vitesse sur un tour de qualification, avec ses sections rapides et ses zones de freinage | Data | Python, numpy, matplotlib | Terminé (v1) |
| [Usure des pneus F1](./projets/usure-pneus-f1) | Hongrie 2025, Norris contre Piastri : la dégradation des pneus une fois retirés carburant, trafic et neutralisations, et pourquoi les données ne permettent pas de dire si les deux arrêts ont coûté du temps | Data | Python, pandas, statsmodels, matplotlib | Terminé (v1) |

## Comment c'est rangé

```
.
├── README.md                    # cette page
├── .gitignore
├── projets/                     # un dossier par projet
│   ├── moteur-strategie-f1/     # Moteur de stratégie F1
│   ├── risque-undercut-f1/      # Risque d'undercut F1 (réutilise le Moteur de stratégie F1)
│   ├── centre-commande-f1/      # Centre de commande F1 (réutilise les deux précédents)
│   ├── carte-vitesse-f1/        # Carte de vitesse F1 (autonome)
│   └── usure-pneus-f1/          # Usure des pneus F1 (autonome)
└── modele-projet/
    └── README.md                # le modèle de README que je recopie pour chaque nouveau projet
```

Chaque projet contient :
- un `README.md` (contexte, démarche, résultats, limites) ;
- le code ou les notebooks ;
- des captures d'écran quand c'est visuel.

## Ma façon de travailler

- Je pars d'une question concrète, pas d'une techno à la mode.
- Je documente ce qui n'a pas marché autant que ce qui a marché.
- Je note les limites de chaque projet. Un modèle sans ses hypothèses, ça ne veut pas dire grand-chose, surtout en finance.

## Me contacter

- LinkedIn : [linkedin.com/in/victor-bessaguet](https://www.linkedin.com/in/victor-bessaguet/)
- Mail : [victor.bessaguet@outlook.com](mailto:victor.bessaguet@outlook.com)

Un retour, une idée, une erreur repérée dans un projet : ça m'intéresse vraiment.
