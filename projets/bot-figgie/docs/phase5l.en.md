# Phase 5l: a card value that accounts for the time left

*Version française : [phase5l.fr.md](phase5l.fr.md)*

Phase 5k worked around a flaw in the v4c without fixing it. In the first minute, the v4c values a card at $13.50 to $16 when it gives the card's suit only a 25 to 30 % chance of being the goal. The card itself is worth about $2.50. The rest comes from the majority, which the marginal bot's value counts as if nobody traded afterwards. Phase 5k banned buying for 60 s. The bot then won its trades, but lost the majority. This phase fixes the value itself.

In the tournament, the new v4c is the project's best bot against the zoo. With 4 players it earns $9.74 per round against the marginal bot and $15.18 against the recalibrated Hard bot, against $7.26 and $10.06 for phase 5k's selling v4c. It is also the first candidate to pass the entry rule with 4 players. But it is refused with 5 players: at the mixed table, the v4c that stays quiet in the first minute does $2.46 per round better than it, and the reading exploiter $1.66. No bot is promoted.

## Separating the card from the majority

When a goal card changes hands, my final gain changes for two reasons. The card itself is worth $10. And my share of the rest of the pot can change: one more card can give me the majority, one card fewer can make me lose it. Until now, the value counted both in full, whatever the time in the round.

At the start of the round, though, the majority is far from settled. There are still three or four minutes of trading left, and a card bought now guarantees nothing at the bell. So I keep the card's part in full, and I multiply the majority part by a weight that rises with time:

w(t) = min(1, t / T) ^ k

At the start of the round, w is 0: a goal card is worth $10 times the probability that its suit is the goal. From T seconds on, w is 1 and the value is the same as today. k sets how fast it rises.

The weight applies to buying and to selling. That choice has a possible cost: early in the round, a goal card is also worth less when selling, and phase 5k showed that selling goal cards early loses the majority. The tournament would tell whether that cost wins.

So as not to rerun the Monte Carlo every turn, the weight is rounded to the nearest twentieth: the value is recomputed only about twenty more times per round.

The seams, written with TDD:
- with a weight of 0 and a goal suit known for sure, a card of that suit is worth exactly $10 to buy and to sell, and a card of the other suits $0. With the majority, it is worth more than $10. The test catches a majority that is removed the wrong way (I broke it by multiplying the whole gain by the weight: it fails);
- with a weight of 1, the values are today's, with the same seed. The test catches a random draw that would change with the weight. The code review found a flaw in it: my first version compared two calls with a weight of 1, which both went through the weight-1 shortcut, so it could not see a draw that depends on the weight. I now use a weight just below 1, and the test fails when I add one extra draw whenever the weight is not 1. Existing bots still go through the shortcut: they keep exactly their results, and the engine's reference test does not move;
- under the site rule, in each round the bot plays the setting its retrained model gives, read directly from the model file. My first version of the test compared the bot with its own choice method: it passed even when I broke that choice. I rewrote it, and it now fails if the bot keeps its starting setting, or if it reads the v4c's model.

## Choosing T and k

I set the criterion before running: the highest mean of the gain against three recalibrated Hard bots and the gain against three marginal bots. Seed 9 (never the tournament's seed 1), 100 duplicate deals, 10-round games with 4 players, site rule, with the v4c's settings and no retraining:

| Bot | against 3 recalibrated Hard | against 3 marginal | mean |
|---|---|---|---|
| v4c | -6.76 [-8.41; -5.11] | +8.50 [+7.58; +9.42] | +0.87 |
| selling v4c (5k) | +7.51 [+5.86; +9.16] | +7.76 [+6.78; +8.74] | +7.63 |
| T = 60 s, k = 0.5 | +12.93 [+11.17; +14.70] | +9.15 [+8.16; +10.14] | +11.04 |
| T = 60 s, k = 1 | +13.04 [+11.51; +14.56] | +8.96 [+7.96; +9.96] | +11.00 |
| T = 60 s, k = 2 | +7.64 [+6.14; +9.14] | +9.18 [+8.14; +10.22] | +8.41 |
| T = 120 s, k = 0.5 | **+15.52 [+13.83; +17.21]** | **+10.80 [+9.83; +11.77]** | **+13.16** |
| T = 120 s, k = 1 | +10.53 [+9.02; +12.03] | +10.09 [+9.12; +11.07] | +10.31 |
| T = 120 s, k = 2 | +5.84 [+4.46; +7.22] | +10.77 [+9.69; +11.85] | +8.31 |
| T = 240 s, k = 0.5 | +13.46 [+11.89; +15.03] | +12.25 [+11.15; +13.34] | +12.85 |
| T = 240 s, k = 1 | +5.77 [+4.46; +7.08] | +12.30 [+11.25; +13.35] | +9.03 |
| T = 240 s, k = 2 | -0.70 [-1.83; +0.42] | +13.53 [+12.50; +14.55] | +6.41 |

All nine points beat the v4c, against the recalibrated Hard bots and against the marginal bots. The later the majority comes back (large T, large k), the better the bot plays against the marginal bots, and the worse against the recalibrated Hard bots. The point I kept, T = 120 s and k = 0.5, gives a majority that already counts for half after 30 s, 71 % after one minute, and in full from 2 minutes on.

## Retraining the settings

The v4c's settings (spread and edge, chosen by its neighbours) were learned with the old value. I learned them again with the new one, on exactly the same 188 tables as the v4c's model, in the same order: the 80 tables of the v4's second round, the 24 full tables of the v4b and the 84 symmetric tables of the v4c. Only the value of the settings played changes. To check that I was replaying the same tables, I first reran the first table of each kind with no weight: all three are identical to the ones in the v4c's report.

In cross-validation (each table judged by a model built on the others), the chosen setting earns $3.76 per round more than the fixed setting [+3.24; +4.27], against $2.48 for the v4c. The best possible setting earns $5.05 more. On these tables, the new value earns more with the fixed setting ($10.83 against $9.74), and choosing the setting adds a little more.

I put two candidates in the tournament: `v4c_temps`, with its retrained settings, and `v4c_temps_brut`, the same value with the v4c's settings. The gap between them measures what retraining brings.

## The tournament

Same format as phases 5j and 5k: seed 1, 100 deals of 10 rounds, the recalibrated Hard bot as the mixed table's filler. I added a twelfth reference to the mixed table, phase 5k's selling v4c. Since the deals are the same as in phase 5k, the numbers compare directly.

Against three copies of the same opponent (the candidate's gain, in dollars per round):

| Opponent | timed v4c, 4 p. | timed v4c, 5 p. | no retraining, 4 p. | no retraining, 5 p. | selling v4c, 4 p. (5k) |
|---|---|---|---|---|---|
| heuristic | +42.09 [+39.73; +44.46] | +36.78 [+34.96; +38.60] | +39.32 | +35.34 | +36.47 |
| sniper | +30.85 [+29.55; +32.14] | +27.50 [+26.25; +28.75] | +30.85 | +27.50 | +25.86 |
| Bayesian | +23.68 [+21.69; +25.67] | +22.20 [+20.63; +23.77] | +22.61 | +21.22 | +23.08 |
| marginal | +9.74 [+8.81; +10.67] | +8.04 [+7.31; +8.76] | +10.39 | +7.10 | +7.26 |
| phase 5c Hard | +37.40 [+36.00; +38.79] | +31.86 [+30.79; +32.93] | +36.18 | +33.75 | +36.96 |
| recalibrated Hard | +15.18 [+13.39; +16.97] | +12.78 [+11.49; +14.08] | +15.95 | +15.26 | +10.06 |

At the mixed table (reference minus candidate, in dollars per round; a gap whose whole interval is above 0 refuses the candidate):

| Reference | timed v4c, 4 p. | timed v4c, 5 p. | no retraining, 4 p. | no retraining, 5 p. |
|---|---|---|---|---|
| recalibrated Hard | -19.96 [-22.48; -17.44] | -16.36 [-18.08; -14.64] | -21.41 [-23.98; -18.85] | -19.15 [-20.98; -17.32] |
| Bayesian | -24.55 [-26.19; -22.92] | -20.14 [-21.54; -18.75] | -24.00 [-25.76; -22.25] | -19.18 [-20.72; -17.64] |
| marginal | -15.13 [-16.87; -13.39] | -11.80 [-13.27; -10.33] | -10.89 [-12.63; -9.14] | -10.79 [-12.15; -9.43] |
| v3 | -10.65 [-12.54; -8.77] | -8.66 [-10.23; -7.09] | -8.05 [-9.87; -6.24] | -7.82 [-9.42; -6.22] |
| v4b | -7.64 [-9.26; -6.02] | -1.79 [-3.22; -0.36] | -7.92 [-9.50; -6.33] | -4.85 [-6.28; -3.43] |
| v4c | -7.27 [-8.84; -5.70] | -1.74 [-3.18; -0.30] | -7.09 [-8.80; -5.38] | -4.80 [-6.22; -3.39] |
| quiet v4c 60 s | -1.33 [-2.47; -0.19] | **+2.46 [+1.51; +3.41]** | +1.14 [-0.02; +2.29] | **+1.61 [+0.63; +2.58]** |
| selling v4c (5k) | -3.49 [-4.63; -2.34] | +0.45 [-0.47; +1.36] | -2.21 [-3.29; -1.14] | -1.91 [-2.75; -1.07] |
| exploiter | -17.50 [-19.07; -15.93] | -14.69 [-15.87; -13.51] | -20.25 [-21.98; -18.52] | -16.95 [-18.34; -15.57] |
| reading exploiter | -6.97 [-8.63; -5.32] | **+1.66 [+0.23; +3.08]** | -5.08 [-6.77; -3.40] | **+1.99 [+0.78; +3.19]** |
| seller | -14.35 [-15.52; -13.19] | -9.55 [-10.74; -8.36] | -13.17 [-14.41; -11.94] | -11.35 [-12.57; -10.12] |
| gambler | -13.53 [-15.46; -11.60] | -12.82 [-14.15; -11.48] | -14.69 [-16.68; -12.71] | -13.88 [-15.37; -12.38] |

With 4 players, the timed v4c passes: every gap is below 0, and the closest one, -$1.33 against the quiet v4c, has its whole interval below 0. It is the first time since the mixed table became part of the entry rule (phase 5i). With 5 players, two references refuse it, the same as in phase 5k, with smaller gaps.

Against the zoo, it does better than the selling v4c almost everywhere, and clearly against the recalibrated Hard bot (+$15.18 against +$10.06) and the marginal bot (+$9.74 against +$7.26). So the flaw phase 5k aimed at is now fixed by the value itself, without banning purchases.

Retraining brings nothing clear. Both versions are refused by the same references with 5 players, with close gaps. Against the zoo, the retrained version earns a little more against the heuristic and the marginal bot with 5 players, and a little less against the recalibrated Hard bot. Its cross-validation promised $1.3 more per round from choosing the setting, on its training tables: it does not show in the tournament.

## What the two references take from it with 5 players

I had each of the two references play the timed v4c and three recalibrated Hard bots, over 40 games of 10 rounds, in both seat orders. As in phase 5k, for each trade I count what the seller gains on the buyer: the price minus the card's final value. And I count who ends with the most goal cards. Per round, the three Hard bots together:

| Table | reference's gain | timed v4c's gain | reference's majority | timed v4c's majority |
|---|---|---|---|---|
| quiet v4c 60 s | -1.08 | -6.13 | 31.8 % | 21.1 % |
| reading exploiter | +1.70 | +0.94 | 40.0 % | 15.5 % |

Against the quiet v4c, trades play almost no part: $0.48 per round passes between the two of them. And the quiet v4c even loses more on its trades with the Hard bots ($13.86 per round, nearly all in the second minute, against $8.06). It gets ahead through the majority: 31.8 % of rounds against 21.1 %.

Against the reading exploiter, the money does go through trades: it takes $9.00 per round from the timed v4c during the first minute, and almost nothing afterwards. In that first minute, it buys 0.61 goal cards per round, and the timed v4c sells 0.59.

Both tables show the same flaw: the timed v4c sells its goal cards. Over a round, it sells 1.14 and buys 0.68 at the quiet v4c's table, while the quiet v4c does the opposite (0.61 sold, 0.88 bought). That is the cost I feared when I put the weight on the selling side: early in the round, a goal card is worth to it only $10 times the chance that its suit is the goal, and it gives the card away at that price to a player who does count the majority. Phase 5k stopped on the same finding: you win your trades, and you lose the majority.

These are plain games, with no duplicate deals and no confidence interval: they show where to look, they do not measure the gap.

## Does the bot progress?

Not in the entry rule's sense: the timed v4c is refused with 5 players, and the marginal bot stays the reference bot. But it is the candidate that comes closest. It passes with 4 players, which no candidate had done since phase 5i. With 5 players, its worst gap is +$2.46 per round, against +$3.43 for the selling v4c in phase 5k, on the same deals. And it beats the marginal bot and the recalibrated Hard bot by more than any earlier candidate.

These gains are measured against simulated bots: they are not real gains on figgie.com.

Since it is refused with 5 players, I did not run the full tournament (300 deals, 19 references) planned in case it passed at both table sizes.

## Limits

T and k are chosen on a grid of nine points, with 4 players only, against two kinds of tables. I did not look for a different weight with 5 players.

The weight depends only on time. It does not account for what the bot already knows about the goal, nor for how many cards are left to trade.

The 5-player diagnostic uses plain games, with scripts outside the repository, like the grid and the check of the training tables.

The tournament is reduced like those of phases 5j and 5k: 100 deals instead of 300, and part of the references. The intervals are about 1.7 times wider than in phase 5i.

Everything is still measured against simulated bots. These gains are not real gains on figgie.com.

## Reproduce

```bash
cd projets/bot-figgie
python3 -m unittest                                                  # the 138 tests, about 5 s
python3 -m figgie.adapt --v4t 120,0.5 --deals 40 --rounds 3 \
    --arms 6,3,6,3 8,1,8,1 10,3,10,3 12,3,12,3 8,1,3,1 12,3,4,1 --report entrainement_v4t.json
python3 -m figgie.tournoi --site --candidates v4c_temps v4c_temps_brut --rounds 10 --deals 100 --no-tables \
    --opponents heuristique sniper bayesien marginal hard_simule hard_simule_v2 --references \
    --mixed hard_simule_v2 bayesien marginal adaptatif_v3 adaptatif_v4b adaptatif_v4c v4c_calme_60 v4c_vente_60 \
        exploiteur exploiteur_lecteur vendeur parieur --out tournoi.json
```

Retraining takes about 4 h on 10 cores and rewrites `modeles/adaptation_v4t.json`. The tournament takes about 4 h 10. To get back exactly this phase's code: `git checkout phase5l-figgie`.
