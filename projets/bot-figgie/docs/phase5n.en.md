# Phase 5n: the majority weight on the buying side only

*Version française : [phase5n.fr.md](phase5n.fr.md)*

In phase 5l, the majority share in a card's value got a weight that rises with time. The weight applied to buying and selling alike. Phase 5l's diagnostic showed the price of that choice: with 5 players, the bot sold its goal cards early in the round, because a goal card was then worth only $10 times the chance that its suit is the goal. Players who count the majority in full bought them back. This phase keeps the weight on buying, where it stops the bot from overpaying for cards in the first minute, and removes it from selling.

Result: the candidate passes the entry rule with 4 and with 5 players, in the reduced tournament and in the full 300-deal one. No candidate had done so since the rule moved to the mixed table, in phase 5i. It is promoted and replaces the marginal bot as the reference bot. Two caveats: with 5 players, it only ties with the reading exploiter, and it gains less than the previous version against marginal bots. These gains are measured against simulated bots, not on the site.

## The change

`marginal_values` gets a `weight_sell` parameter. When it is `False`, the buy value keeps the time-weighted majority share, and the sell value counts the majority in full, as before phase 5l. The new candidate, `v4c_achat`, is the v4c with this setting. It is not retrained: it plays with the v4c's settings, which phase 5m learned again on the fixed code.

Two seams, written with TDD on one hand and one draw:
- with the weight on buying only, every sell value is exactly the unweighted one;
- every buy value is exactly phase 5l's, with the weight on both sides. The test also checks that, in that case, the weight does change at least one sell value: otherwise the first seam could not see anything.

Both tests failed before the code. I then checked that they catch two deliberate mistakes: putting the weight back on selling, and removing it from buying.

## Choosing T

The weight stays min(1, t / T) ^ 0.5, with k = 0.5 as in 5l. I tried T = 60, 120 and 240 seconds. This time I measured with 4 and with 5 players, since phase 5l failed with 5.

The criterion, set before the run: the mean of four gains (against three recalibrated Hard bots and against three marginal bots, with 4 and 5 players), minus the quiet v4c's gap at the mixed table with 5 players. That was the reference that refused the bot in phase 5m. Seed 9 (never the tournament's seed 1), 100 duplicate deals, games of 10 rounds, site rule, the v4c's settings for every bot.

| Bot | 3 recal. Hard, 4 p. | 3 recal. Hard, 5 p. | 3 marginal, 4 p. | 3 marginal, 5 p. | quiet v4c, mixed table, 5 p. | score |
|---|---|---|---|---|---|---|
| v4c | -5.83 [-7.62; -4.05] | -4.35 [-5.93; -2.77] | +8.45 [+7.63; +9.28] | +4.90 [+3.98; +5.83] | +5.78 [+4.74; +6.83] | -4.99 |
| weight on both sides, T = 120 s (5l) | +16.67 [+14.89; +18.45] | +14.80 [+13.32; +16.27] | +12.80 [+11.65; +13.94] | +10.31 [+9.31; +11.30] | +1.84 [+0.79; +2.90] | +11.80 |
| buying only, T = 60 s | +9.10 [+7.30; +10.90] | +14.81 [+13.09; +16.53] | +10.85 [+9.81; +11.90] | +6.86 [+5.95; +7.76] | +1.81 [+0.69; +2.93] | +8.60 |
| buying only, T = 120 s | +16.08 [+14.29; +17.87] | +17.65 [+16.42; +18.88] | +11.80 [+10.78; +12.82] | +7.32 [+6.47; +8.16] | +0.65 [-0.34; +1.63] | +12.57 |
| **buying only, T = 240 s** | **+17.94 [+16.35; +19.53]** | **+15.25 [+13.84; +16.66]** | **+13.61 [+12.54; +14.68]** | **+9.21 [+8.37; +10.05]** | **-0.00 [-0.98; +0.97]** | **+14.01** |

The criterion picks T = 240 s. It is also the only point where the quiet v4c no longer does better than the candidate at the mixed table: the gap is zero, with an interval centred on 0. With T = 240 s, the majority counts on the buying side at half after one minute, at 71 % after two, and in full only at the bell.

Weighting the buying side only does not win everywhere. With 5 players against the marginal bots, the weight on both sides does better (+$10.31 against +$9.21). The gap against the quiet v4c is what makes the difference in score.

## The reduced tournament

Same format as phase 5m: seed 1, 100 deals of 10 rounds, site rule, with the recalibrated Hard as the mixed-table filler. I added a 13th reference, phase 5l's timed v4c, to measure the candidate directly against the bot it wants to replace. This time only the candidate changes: no other bot reads the new parameter, so every opponent plays exactly as in phase 5m. The gap between the two columns comes from the candidate.

Against three copies of one opponent (candidate's gain, in dollars per round):

| Opponent | 5n, 4 p. | 5n, 5 p. | 5m, 4 p. | 5m, 5 p. |
|---|---|---|---|---|
| heuristic | +42.70 [+40.62; +44.77] | +38.32 [+36.73; +39.92] | +42.48 | +37.54 |
| sniper | +32.67 [+31.24; +34.10] | +29.94 [+28.73; +31.15] | +33.81 | +31.51 |
| Bayesian | +25.89 [+24.07; +27.72] | +25.48 [+23.86; +27.10] | +24.31 | +23.41 |
| marginal | +13.31 [+12.43; +14.19] | **+8.92 [+8.05; +9.79]** | +12.19 | **+12.40** |
| phase 5c Hard | +43.00 [+41.59; +44.41] | +38.29 [+37.13; +39.44] | +38.24 | +34.40 |
| recalibrated Hard | +17.58 [+16.00; +19.16] | +15.91 [+14.55; +17.27] | +15.26 | +13.13 |

At the mixed table (reference minus candidate, in dollars per round; a gap whose whole interval is above 0 rejects the candidate):

| Reference | 5n, 4 p. | 5n, 5 p. | 5m, 4 p. | 5m, 5 p. |
|---|---|---|---|---|
| recalibrated Hard | -23.45 [-25.69; -21.21] | -20.31 [-22.05; -18.56] | -20.61 | -16.28 |
| Bayesian | -29.85 [-31.65; -28.04] | -22.49 [-23.98; -21.01] | -21.94 | -18.97 |
| marginal | -18.88 [-20.75; -17.02] | -13.42 [-15.28; -11.55] | -14.67 | -10.54 |
| v3 | -13.45 [-15.46; -11.44] | -10.22 [-12.23; -8.21] | -9.96 | -6.30 |
| v4b | -13.25 [-14.74; -11.75] | -7.53 [-8.96; -6.10] | -8.36 | -1.68 |
| v4c | -15.64 [-17.03; -14.26] | -8.82 [-10.18; -7.46] | -8.08 | -2.64 |
| quiet v4c, 60 s | -3.85 [-5.12; -2.57] | -1.85 [-3.02; -0.67] | -1.09 | **+3.05** |
| selling v4c (5k) | -5.80 [-6.83; -4.77] | -3.21 [-4.14; -2.28] | -3.07 | +0.02 |
| exploiter | -19.24 [-20.85; -17.64] | -15.05 [-16.30; -13.80] | -17.24 | -15.90 |
| reading exploiter | -10.99 [-13.00; -8.97] | +0.34 [-1.08; +1.75] | -6.64 | +0.22 |
| seller | -17.65 [-18.92; -16.38] | -12.66 [-13.75; -11.57] | -15.42 | -10.25 |
| gambler | -17.11 [-18.89; -15.33] | -16.02 [-17.47; -14.56] | -13.02 | -12.77 |
| timed v4c (5l) | -4.45 [-5.56; -3.33] | -3.29 [-4.15; -2.43] | | |

The candidate passes the entry rule with 4 and with 5 players. It is the first time a candidate passes at both table sizes since the entry rule moved to the mixed table, in phase 5i. The quiet v4c, which rejected the timed v4c with 5 players, now ends $1.85 behind the candidate, with an interval entirely below 0. Against the timed v4c itself, the candidate gains $4.45 per round with 4 players and $3.29 with 5.

Two caveats. The reading exploiter still ties with 5 players (+$0.34, with an interval that contains 0): the rule passes because it only rejects what is clearly ahead, not because the candidate beats it. And against three marginal bots with 5 players, the candidate loses more than $3 per round compared with phase 5m (+$8.92 against +$12.40, intervals that do not touch). The grid already showed it: with 5 players against marginal bots, keeping the weight on selling pays more. I have not checked where this loss comes from.

## The full tournament

Since the candidate passed at both sizes, I ran the full tournament: seed 1, 300 deals of 10 rounds, and every reference at the mixed table, phase 5i's plus the recalibrated Hard, the v4c, the quiet v4c, the selling v4c and the timed v4c. The last full tournament was phase 5i's, on different code, so I do not compare its numbers with these.

Against three copies of one opponent (candidate's gain, in dollars per round):

| Opponent | 4 p. | 5 p. |
|---|---|---|
| heuristic | +41.39 [+40.30; +42.48] | +39.23 [+38.33; +40.12] |
| sniper | +32.24 [+31.43; +33.06] | +30.05 [+29.39; +30.71] |
| Bayesian | +25.73 [+24.71; +26.75] | +25.45 [+24.48; +26.41] |
| marginal | +13.00 [+12.47; +13.53] | +9.16 [+8.66; +9.66] |
| phase 5c Hard | +41.71 [+40.86; +42.56] | +38.00 [+37.35; +38.66] |
| recalibrated Hard | +17.83 [+16.91; +18.75] | +16.55 [+15.75; +17.34] |

At the mixed table (reference minus candidate, in dollars per round):

| Reference | 4 p. | 5 p. |
|---|---|---|
| phase 5c Hard | -84.61 [-85.97; -83.25] | -81.39 [-82.48; -80.30] |
| heuristic | -72.11 [-73.44; -70.77] | -58.62 [-59.81; -57.44] |
| imitator | -31.80 [-33.21; -30.39] | -38.47 [-39.74; -37.20] |
| fundamentalist (r = 3.5) | -35.57 [-36.61; -34.52] | -29.36 [-30.20; -28.52] |
| sniper | -33.71 [-34.67; -32.75] | -26.58 [-27.43; -25.73] |
| Bayesian | -30.48 [-31.55; -29.41] | -22.69 [-23.57; -21.81] |
| mantis | -25.36 [-26.24; -24.47] | -22.69 [-23.46; -21.92] |
| fundamentalist (r = 1.7) | -25.43 [-26.63; -24.24] | -20.91 [-21.76; -20.07] |
| recalibrated Hard | -23.66 [-24.96; -22.37] | -20.92 [-21.95; -19.89] |
| exploiter | -19.44 [-20.38; -18.51] | -15.21 [-15.96; -14.45] |
| marginal | -18.54 [-19.65; -17.43] | -14.42 [-15.42; -13.43] |
| gambler | -16.78 [-17.76; -15.80] | -16.44 [-17.24; -15.64] |
| seller | -17.62 [-18.35; -16.90] | -13.09 [-13.74; -12.44] |
| v3 | -14.29 [-15.46; -13.12] | -10.26 [-11.31; -9.21] |
| v4c | -13.75 [-14.59; -12.92] | -9.05 [-9.80; -8.31] |
| v4b | -12.04 [-12.94; -11.14] | -7.61 [-8.40; -6.82] |
| selling v4c (5k) | -5.97 [-6.57; -5.36] | -3.70 [-4.21; -3.19] |
| timed v4c (5l) | -3.90 [-4.49; -3.30] | -4.25 [-4.76; -3.74] |
| quiet v4c, 60 s | -3.63 [-4.30; -2.96] | -1.19 [-1.85; -0.53] |
| reading exploiter | -10.10 [-11.20; -9.00] | -0.10 [-0.95; +0.74] |

The candidate passes the entry rule with 4 and with 5 players, with three times more deals and seven more references. With 4 players, it ends ahead of all 20 references, with an interval entirely below 0. With 5 players, it ends ahead of 19 of them. The reading exploiter ties with it: -$0.10, with an interval that contains 0. The reduced tournament's numbers hold: the quiet v4c stays behind, and so does the loss against marginal bots with 5 players (+$9.16 per round).

## Does the bot progress?

Yes, in the sense of the entry rule. For the first time since the rule moved to the mixed table, a candidate passes it at both sizes, in the reduced tournament and in the full one. Against phase 5l's timed v4c, which differs from it only in selling, it gains $3.90 per round with 4 players and $4.25 with 5. Against the recalibrated Hard bots, the closest I have to the site's bots, it gains $2 to $3 more per round than the timed v4c.

So I promote it: `v4c_achat` replaces the marginal bot as the reference bot. It is not an unexploitable bot. It only ties with the reading exploiter with 5 players, and it gains less than the timed v4c against marginal bots with 5 players. The next phase will search for exploiters against it.

These gains are measured against simulated bots: they are not real gains on figgie.com.

## Limits

T was chosen on seed 9 among only three values, with k kept at 0.5. A value above 240 s was not tried, although the score was still rising from 120 to 240 s.

The candidate is not retrained: it plays with the settings the v4c learned, whose value also weights selling. Settings learned with the new value could be different.

The automatic exploiter search has not been rerun since phase 5b. The entry rule only tests the references I wrote or borrowed: an opponent built against this bot could beat it.

I have not checked why the candidate gains less against marginal bots with 5 players.

Everything is still measured against simulated bots. These gains are not real gains on figgie.com.

## Reproduce

```bash
cd projets/bot-figgie
python3 -m unittest                                                  # the 144 tests, about 7 s
python3 -m figgie.tournoi --site --candidates v4c_achat --rounds 10 --deals 100 --no-tables \
    --opponents heuristique sniper bayesien marginal hard_simule hard_simule_v2 --references \
    --mixed hard_simule_v2 bayesien marginal adaptatif_v3 adaptatif_v4b adaptatif_v4c v4c_calme_60 v4c_vente_60 \
        exploiteur exploiteur_lecteur vendeur parieur v4c_temps --out tournoi.json
python3 -m figgie.tournoi --site --candidates v4c_achat --rounds 10 --deals 300 --no-tables \
    --opponents heuristique sniper bayesien marginal hard_simule hard_simule_v2 --references \
    --mixed hard_simule heuristique sniper bayesien marginal adaptatif_v3 adaptatif_v4b exploiteur \
        exploiteur_lecteur imitateur fondamentaliste fondamentaliste_35 vendeur mante parieur \
        hard_simule_v2 adaptatif_v4c v4c_calme_60 v4c_vente_60 v4c_temps --out tournoi_complet.json
```

On 10 cores, the reduced tournament took 2 h 24 and the full one 11 h 32. The grid that chose T is a script outside the repository; its output is in `resultats/phase5n/grille_graine9.txt`. To get this phase's exact code back: `git checkout phase5n-figgie`.
