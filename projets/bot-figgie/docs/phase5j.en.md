# Phase 5j: a simulated Hard bot that no longer overpays

*Version française : [phase5j.fr.md](phase5j.fr.md)*

Phase 5i ended on a surprise: at a table of simulated Hard bots, the exploiter, a plain Bayesian bot that quotes tight, did about $10 better per round than the v4c. It sold non-goal cards to the Hard bots at around $10. A first look at Rasmus's real rounds suggested that the site's real bots do not pay that much for these cards. This phase checks that point, then recalibrates the simulated Hard bot and replays the entry rule with it.

The simulated Hard bot was far too generous a buyer. Recalibrated, it almost never takes expensive non-goal asks, like the site's real bots. Against it, the exploiter and the Bayesian bot lose money, and the v4c that stays quiet during the first minute becomes the best of my bots.

In the tournament, neither candidate passes the entry rule, and no bot is promoted. The v4c is refused by the recalibrated Hard bot itself: at the mixed table, it does $9.86 better than the v4c per round with 4 players. The v4c that stays quiet for 60 s does better than every reference at the mixed table with 4 players, but it no longer beats the marginal bot against three of its copies (-$0.06 per round with 4 players, -$3.44 with 5), and the reading exploiter does $4.57 better than it with 5 players.

## Do the site's real bots take asks at $10?

For each ask that became the best of its suit, I looked at how it ends: taken by someone, replaced by a cheaper ask, cancelled, cleared by a trade (after every trade, the site empties the whole book, in all four suits), or still there at the end of the round. I made the same measurement on Rasmus's 60 real rounds and on simulated rounds, one bot alone against three simulated Hard bots. Share of asks taken by a Hard bot, in non-goal suits:

| Ask price | real rounds (asks of Rasmus's bot) | simulation (asks of the exploiter) | simulation (asks of the v4c) |
|---|---|---|---|
| $7 to $8 | 1 % of 1119 | 36 % of 228 | 30 % of 880 |
| $9 to $10 | 1 % of 594 | 18 % of 2106 | 17 % of 547 |
| $11 to $13 | 0 % of 787 | 9 % of 2157 | 11 % of 455 |

On the site, an ask at $7 or more in a non-goal suit is almost never taken: it is replaced by a cheaper ask (60 to 70 % of cases) or cleared by a trade (29 to 38 %). My simulated Hard bots took 9 to 36 % of them depending on the price, and that is where most of the exploiter's gain came from.

The site's log tells apart the cancellation of a bid from that of an ask. My engine removes both sides at once. On the real rounds, I therefore count only the ask cancellations. Cancellations are rare: 0 to 5 % of asks.

## The recalibrated Hard bot

In phase 5c, I tuned the simulated Hard bot on the trades between Hard bots: how many, when in the round, at what prices, and how often they quote. I never looked at how they react to an expensive ask. I added to these measurements the share of a Hard bot's asks that another Hard bot takes, in six price and suit brackets, and ran the same random search again: 3000 settings on 30 rounds, the 10 best checked again on 90 other rounds.

The chosen setting does not need a new parameter. It gives less value to the goal suit ($16 instead of $30 for a probability of 1), it almost agrees with the other Hard bots on the value of the cards (a random offset with a standard deviation of $1 instead of $6), and its margin is smaller ($3 instead of $6) and shrinks faster over the round. Share of a Hard bot's asks that another Hard bot takes:

| | real rounds | recalibrated Hard | phase 5c Hard |
|---|---|---|---|
| non-goal, $1 to $3 | 30 % | 25 % | 7 % |
| non-goal, $7 to $8 | 1.5 % | 2.0 % | 10.4 % |
| non-goal, $9 to $13 | 1.0 % | 0.5 % | 4.8 % |
| goal, $7 to $10 | 11.8 % | 12.2 % | 13.3 % |

There is a price. The recalibrated Hard bot trades less with the other Hard bots than the site's real bots do (5.3 trades per pair and per round, against 9.4; the phase 5c one made 6.5) and quotes more often (59 quotes per minute, against 38). On the phase 5c measurements, its distance to the site goes from 15.7 to 22.4. It would no longer pass the phase 5c resemblance test, which requires each measurement to stay between 0.6 and 1.5 times the site's: its trades between Hard bots are at 0.56 times. So I keep the old Hard bot as it is, as an opponent, and add the new one under the name `hard_simule_v2`.

Against the exploiter, it now behaves like the real bots against Rasmus: the exploiter's non-goal asks at $9 or $10 are taken only once in a hundred.

The seam for this measurement is the function that says how each ask ends. I tested it on a hand-written feed, with one ask taken, one replaced, one cancelled, one cleared and one still there at the end. To check that the test can fail, I broke it on purpose by accepting any trade in the suit as "taken", and it failed.

The code review found two errors in my first version of this function. It only closed the ask of the traded suit, while a trade empties the whole book: an ask in another suit stayed "on screen" in my measurement, and a later trade at its price could pass for a lift. And it counted the cancellation of a bid as that of the ask. I added to the test a feed that covers both cases, watched the test fail, then fixed the code. The shares taken barely moved (30.4 % becomes 30.0 % for asks at $1 to $3, the rest within 0.1 point). The share of "replaced" asks went down, in favour of "cleared" ones. I reran the recalibration with the fixed measurement: it keeps the same setting, with the same ten best in the same order. The recalibrated Hard bot, and so the tournament, do not change.

## Against the recalibrated Hard bot

Each bot alone against three recalibrated Hard bots, over 40 matches of 10 rounds with 4 players, always in the same seat (these plain matches are noisier than a tournament with duplicate deals). Gain per round:

| Bot | against the recalibrated Hard | against the phase 5c Hard |
|---|---|---|
| v4c quiet for 60 s | **+12.56** | |
| v4c quiet for 30 s | +3.49 | |
| v3 | -3.61 | |
| marginal | -6.16 | |
| v4c | -9.18 | +32.81 |
| exploiter | -12.33 | +46.68 |
| Bayesian | -28.73 | |

The empty cells were not measured in these plain matches. The ranking flips. The exploiter, which lived off its sales to the Hard bots, now loses $12 per round. The v4c loses too, and its breakdown shows why: it buys 2.6 non-goal cards per round in the first minute, at around $10, and loses $20 per round on them. The majority brings it $41, but not enough to make up for it.

The v4c that sends no order during the first minute has existed since phase 5g, inspired by the paper by DiSilvio, Luo and Ozerov (arXiv 2110.00879), who found that trading early is costly. In phase 5g, against the old Hard bot, it lost about $8 per round against the marginal bot, and I had set it aside. Against the recalibrated Hard bot, it does $22 per round better than the v4c.

This ranking matches the one from the paper replay of real rounds in phase 5e: all my bots lost there, the v4 was the best and the Bayesian bot the last.

## The mixed table with the recalibrated Hard bot

The mixed table of the entry rule now uses the recalibrated Hard bot as its filler. I first checked what it gives on 50 deals from seed 7. Gap reference minus candidate, in dollars per round:

| | marginal, 4 p. | marginal, 5 p. | v4c, 4 p. | v4c, 5 p. | v4c quiet 60 s, 4 p. | v4c quiet 60 s, 5 p. |
|---|---|---|---|---|---|---|
| exploiter | +1.34 [-1.35 ; +4.02] | +1.27 [-0.37 ; +2.91] | -6.65 [-9.60 ; -3.70] | -5.02 [-7.76 ; -2.29] | -13.97 [-16.36 ; -11.58] | -13.95 [-16.16 ; -11.75] |
| Bayesian | +1.46 [-1.50 ; +4.43] | -4.97 [-7.66 ; -2.29] | -1.92 [-5.26 ; +1.42] | -4.18 [-7.43 ; -0.92] | -16.57 [-19.61 ; -13.54] | -19.59 [-22.45 ; -16.72] |

With this filler, the exploiter no longer does clearly better than the marginal bot. The exploitation that the minority test found in phase 4 came from the majority race between copies (phase 5i), and what the phase 5i mixed table added to it came from the overly generous Hard bot. Not much is left of the exploiter.

## The tournament

I replayed the entry rule with the recalibrated Hard bot as the filler, on seed 1 as in phase 5i. The recalibrated Hard bot is about 1.75 times slower than the old one, so I cut the tournament down to fit in one night: 100 deals of 10 rounds instead of 300, and 10 references at the mixed table instead of 15. I left out the heuristic bot, the sniper, the imitator, the two fundamentalists and the mantis, which all lost more than $30 per round against the v4c at the phase 5i mixed table. The intervals are therefore about 1.7 times wider than in phase 5i.

Against three copies of the same opponent (gain of the candidate, in dollars per round):

| Opponent | v4c, 4 p. | v4c, 5 p. | v4c quiet 60 s, 4 p. | v4c quiet 60 s, 5 p. |
|---|---|---|---|---|
| heuristic | +44.58 [+42.64 ; +46.52] | +43.63 [+42.06 ; +45.20] | +36.24 [+34.45 ; +38.02] | +36.59 [+35.23 ; +37.94] |
| sniper | +27.91 [+26.54 ; +29.28] | +26.09 [+24.81 ; +27.36] | +26.25 [+24.83 ; +27.66] | +24.59 [+23.28 ; +25.91] |
| Bayesian | +26.99 [+25.45 ; +28.53] | +28.11 [+26.61 ; +29.62] | +25.40 [+23.69 ; +27.11] | +24.97 [+23.35 ; +26.58] |
| marginal | +7.67 [+6.75 ; +8.58] | +4.17 [+3.43 ; +4.91] | **-0.06 [-0.97 ; +0.84]** | **-3.44 [-4.21 ; -2.67]** |
| phase 5c Hard | +36.57 [+35.03 ; +38.11] | +34.59 [+33.41 ; +35.78] | +39.10 [+37.34 ; +40.85] | +36.76 [+35.54 ; +37.98] |
| recalibrated Hard | -7.65 [-9.23 ; -6.07] | -4.82 [-6.27 ; -3.38] | +12.12 [+10.36 ; +13.88] | +14.33 [+12.63 ; +16.03] |

At the mixed table (gap reference minus candidate, in dollars per round; a gap whose whole interval is above 0 refuses the candidate):

| Reference | v4c, 4 p. | v4c, 5 p. | v4c quiet 60 s, 4 p. | v4c quiet 60 s, 5 p. |
|---|---|---|---|---|
| recalibrated Hard | **+9.86 [+7.64 ; +12.07]** | **+5.64 [+3.73 ; +7.54]** | -16.13 [-18.67 ; -13.59] | -18.35 [-20.60 ; -16.11] |
| Bayesian | +0.48 [-2.06 ; +3.02] | -5.76 [-7.65 ; -3.87] | -16.35 [-18.42 ; -14.28] | -20.33 [-22.09 ; -18.57] |
| marginal | -4.25 [-6.06 ; -2.43] | -2.16 [-3.89 ; -0.44] | -12.02 [-14.26 ; -9.78] | -9.42 [-11.34 ; -7.49] |
| v3 | -0.14 [-1.97 ; +1.69] | **+2.26 [+0.45 ; +4.08]** | -9.54 [-11.77 ; -7.32] | -5.55 [-7.80 ; -3.31] |
| v4b | +0.42 [-0.18 ; +1.01] | +0.47 [-0.06 ; +1.00] | -6.86 [-8.18 ; -5.54] | -5.79 [-7.05 ; -4.53] |
| v4c | | | -7.40 [-8.72 ; -6.08] | -5.34 [-6.61 ; -4.07] |
| exploiter | -5.23 [-6.89 ; -3.57] | -5.46 [-7.17 ; -3.75] | -13.75 [-15.46 ; -12.05] | -13.09 [-14.71 ; -11.48] |
| reading exploiter | **+1.52 [+0.01 ; +3.03]** | **+7.23 [+5.71 ; +8.75]** | -5.77 [-7.87 ; -3.68] | **+4.57 [+2.75 ; +6.39]** |
| seller | +0.47 [-1.03 ; +1.97] | **+2.68 [+1.26 ; +4.09]** | -10.50 [-11.84 ; -9.15] | -8.25 [-9.63 ; -6.87] |
| gambler | -0.92 [-3.30 ; +1.47] | -1.77 [-3.80 ; +0.25] | -13.13 [-15.03 ; -11.22] | -15.34 [-17.23 ; -13.45] |

The verdicts:

- **v4c**: refused with 4 and 5 players. It does beat the four zoo references, but the recalibrated Hard bot and the reading exploiter do better than it at the mixed table, and with 5 players so do the v3 and the seller.
- **v4c quiet 60 s**: refused with 4 and 5 players. With 4 players, only one thing is missing: clearly beating the marginal bot against its copies, and it breaks even. With 5 players, it loses $3.44 per round against the marginal bot's copies, and the reading exploiter does better than it at the mixed table.

Compared with phase 5i, the v4c's numbers against the zoo barely move (+$7.67 against +$7.75 against the marginal bot with 4 players): same opponents and same deal draw, on fewer deals. The mixed table changes a lot. The exploiter goes from +$10.43 to -$5.23 against the v4c with 4 players, and the Bayesian bot from +$7.13 to -$5.76 with 5 players: both phase 5i exploitations disappear with the overly generous Hard bot. But others appear. The reading exploiter goes from -$13.91 to +$1.52, the seller from -$10.08 to +$2.68 with 5 players. These references did not change; the v4c earns less at a table of recalibrated Hard bots, because it overpays them in the first minute.

Does the bot progress? No, in the sense of the entry rule: no candidate passes it, and the marginal bot stays the reference bot. The v4c that stays quiet for 60 s is the most interesting result of the phase: at a table of recalibrated Hard bots, it earns about $20 more per round than the v4c, and at the mixed table, none of the ten references does better than it with 4 players. But against bots that quote from the start, like the marginal bot, staying quiet for a minute costs it what it was earning. These gains are measured against simulated bots: they are not real gains on figgie.com.

## Limits

The recalibrated Hard bot matches the site's real bots on the share of asks taken, but less well than the old one on the number of trades between Hard bots. Both are imitations tuned on 60 rounds of a single player, Rasmus, against the Hard bots. What I measure against them is not what my bots would do on figgie.com.

The comparison of taken asks does not cover the same sellers: on real rounds, these are the asks of Rasmus's bot and of the Hard bots; in simulation, those of my bots and of the simulated Hard bots. A Hard bot could react differently to an ask from the exploiter than to an ask from Rasmus's bot at the same price. Nothing in the logs lets me check that.

The recalibration does not see everything. The price brackets leave out asks above $13 and goal-suit asks at $6 or less. And a setting that posts no ask in a bracket, over the 30 rounds of the search, gets an infinite distance: that is the case for 1964 settings out of 3000. They are set aside for lack of data, not because they look unlike the site.

The plain matches against the recalibrated Hard bot always use the same seat: they are noisier than the tournament.

Everything is still measured against simulated bots. These gains are not real gains on figgie.com.

## Reproduce

```bash
cd projets/bot-figgie
python3 -m unittest                                                  # the 134 tests, about 5 s
python3 -m figgie.calibrate --settings 3000 --rounds 30 --keep 10 --lift --out calibration_hard_v2.json
python3 -m figgie.tournoi --site --seed 7 --candidates marginal adaptatif_v4c v4c_calme_60 --rounds 10 --deals 50 \
    --no-tables --opponents --references --mixed exploiteur bayesien --out calibration.json
python3 -m figgie.tournoi --site --candidates adaptatif_v4c v4c_calme_60 --rounds 10 --deals 100 --no-tables \
    --opponents heuristique sniper bayesien marginal hard_simule hard_simule_v2 --references \
    --mixed hard_simule_v2 bayesien marginal adaptatif_v3 adaptatif_v4b adaptatif_v4c exploiteur exploiteur_lecteur \
        vendeur parieur --out tournoi.json
```

The recalibration takes about 3 min on 10 cores, the calibration 13 min, the tournament about 3 h 30. To get back to the exact code of this phase: `git checkout phase5j-figgie`.
