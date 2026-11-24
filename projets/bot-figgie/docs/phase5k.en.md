# Phase 5k: buying nothing in the first minute

*Version française : [phase5k.fr.md](phase5k.fr.md)*

Phase 5j left two bots, each good on one side. The v4c beats the marginal bot against its copies, but loses against three recalibrated Hard bots: it overpays them in the first minute. The v4c that stays quiet for the first minute wins against the recalibrated Hard bots, but no longer beats the marginal bot. This phase looks for what the v4c gets wrong in the first minute, and tries to remove only that.

In the tournament, the selling v4c beats the four zoo references and the recalibrated Hard bot, with 4 and with 5 players. But it is refused. At the mixed table, the quiet v4c does a little better than it (+$1.81 per round with 4 players, +$1.57 with 5), and so does the reading exploiter with 5 players (+$3.43). No bot is promoted. It is still the candidate that comes closest to the entry rule since the rule exists.

## What the v4c buys in the first minute

I had the v4c play alone against three recalibrated Hard bots, then against three marginal bots, over 40 matches of 10 rounds, and I recorded every time it takes an ask: the price, the value it gives the card, and the probability it gives the suit of being the goal. For the first minute:

| | against recalibrated Hard, non-goal | against recalibrated Hard, goal | against marginal, non-goal | against marginal, goal |
|---|---|---|---|---|
| lifts per round | 1.02 | 0.36 | 0.82 | 0.26 |
| price paid | $9.63 | $12.28 | $11.30 | $12.52 |
| value it gives the card | $13.56 | $16.50 | $16.25 | $17.66 |
| goal probability it gives the suit | 24 % | 30 % | 30 % | 34 % |

In the first minute, the v4c does not know yet which suit is the goal: it gives about the same probability to the right suit and to the others. Since three suits out of four are not the goal, three of its buys out of four are cards that will end up worth $0.

Yet it pays more than $9 for them. A goal card is worth $10 at the end, so with a 25 % chance, the card itself is worth about $2.50. The rest of its value, more than $10, comes from the majority. The marginal bot, which the v4c inherits from, computes what one more card would bring it at the bell if nobody traded afterwards. With three minutes of market still ahead, that value is far too high.

## Buying nothing, but selling

The idea is to keep what the v4c does well in the first minute, its sales, and remove its buys. I compared this version with the v4c and with the quiet v4c, on the same 40 plain matches, always in the same seat. Gain per round:

| Bot | against 3 recalibrated Hard | against 3 marginal |
|---|---|---|
| v4c | -9.18 | +3.74 |
| v4c quiet for 60 s (phase 5g) | +12.56 | -3.42 |
| v4c that buys nothing for 60 s | +8.15 | +3.33 |

Buying nothing in the first minute, while still selling, keeps a good part of what the quiet v4c earns against the Hard bots, and almost everything the v4c earns against the marginal bots.

The quiet v4c lost against the marginal bots for a simple reason: it also lost its first-minute sales, which bring the v4c $11.49 per round against them. The version that buys nothing even gets $14.40 out of them: it no longer spends any turn buying, and sells more. And when the quiet v4c starts playing, at 60 s, it makes the same buys again: 1.49 cards per round at around $9.40, for a loss of $10.40.

## The selling v4c

The new version is called `v4c_vente_60`. It is the v4c, without retraining, for which a card is worth nothing to buy during the first 60 seconds of each round. With a value of $0, it takes no ask and posts no bid. Nothing else changes: it sells, it quotes asks, it cancels its quotes, and it chooses its setting like the v4c.

My first version worked differently, and the code review found a flaw in it. It let the v4c choose its action, then cancelled it if it was a buy. But the v4c chooses only one action per turn, and looks at buys before sales. Every time it wanted to buy, my version did nothing at all, instead of selling. It sold less than the v4c, the opposite of what I wanted. The first tournament and my two checks on seeds 7 and 11 used that version. I fixed it, then reran everything.

The seam is its behaviour in a match played with the site's rule: no buy and no bid before 60 s, at least as many sales and asks before 60 s as the v4c at the same table, and the same setting choice as the v4c. The "at least as many as the v4c" condition comes from the review. My first version missed it (55 sales and asks against 67 for the v4c), and the test caught it before I fixed the code. To check that the test can fail, I also broke it by letting buys through: it fails. The test does not check that after 60 s, it plays exactly like the v4c.

## The tournament

Same format as phase 5j: seed 1, 100 deals of 10 rounds, the recalibrated Hard bot as the mixed-table filler. I added an eleventh reference to the mixed table, the v4c that stays quiet for 60 s: on seed 7, it did better than the first version of the selling v4c with 5 players, and leaving it out would have made the rule easier to pass. Since the deals are the same as in phase 5j, the numbers of the v4c and of the quiet v4c compare directly.

Against three copies of the same opponent (gain of the candidate, in dollars per round):

| Opponent | selling v4c, 4 p. | selling v4c, 5 p. | v4c, 4 p. (5j) | quiet v4c 60 s, 4 p. (5j) |
|---|---|---|---|---|
| heuristic | +36.47 [+34.57 ; +38.38] | +34.33 [+32.98 ; +35.68] | +44.58 | +36.24 |
| sniper | +25.86 [+24.53 ; +27.18] | +24.48 [+23.32 ; +25.63] | +27.91 | +26.25 |
| Bayesian | +23.08 [+21.33 ; +24.84] | +22.03 [+20.40 ; +23.65] | +26.99 | +25.40 |
| marginal | +7.26 [+6.30 ; +8.23] | +4.80 [+3.97 ; +5.62] | +7.67 | -0.06 |
| phase 5c Hard | +36.96 [+35.39 ; +38.54] | +33.53 [+32.39 ; +34.67] | +36.57 | +39.10 |
| recalibrated Hard | +10.06 [+8.31 ; +11.81] | +12.14 [+10.67 ; +13.60] | -7.65 | +12.12 |

At the mixed table (gap reference minus candidate, in dollars per round; a gap whose whole interval is above 0 refuses the candidate):

| Reference | selling v4c, 4 p. | selling v4c, 5 p. |
|---|---|---|
| recalibrated Hard | -13.44 [-15.92 ; -10.96] | -15.34 [-17.22 ; -13.47] |
| Bayesian | -13.78 [-15.73 ; -11.82] | -15.45 [-17.18 ; -13.72] |
| marginal | -13.90 [-15.55 ; -12.26] | -12.21 [-13.78 ; -10.63] |
| v3 | -11.90 [-13.81 ; -9.98] | -8.79 [-10.48 ; -7.10] |
| v4b | -8.67 [-10.05 ; -7.30] | -5.29 [-6.50 ; -4.07] |
| v4c | -8.85 [-10.30 ; -7.41] | -5.79 [-7.04 ; -4.54] |
| quiet v4c 60 s | **+1.81 [+0.69 ; +2.92]** | **+1.57 [+0.61 ; +2.52]** |
| exploiter | -13.27 [-14.84 ; -11.70] | -12.33 [-13.70 ; -10.97] |
| reading exploiter | -4.22 [-5.91 ; -2.53] | **+3.43 [+1.80 ; +5.06]** |
| seller | -8.38 [-9.71 ; -7.05] | -7.17 [-8.47 ; -5.88] |
| gambler | -14.21 [-16.09 ; -12.33] | -14.26 [-15.80 ; -12.73] |

The selling v4c does what I expected against the zoo. It keeps almost everything the v4c earns against the marginal bot (+$7.26 against +$7.67 with 4 players), and a good part of what the quiet v4c earns against the recalibrated Hard bot (+$10.06 against +$12.12). In exchange, it earns $8 less than the v4c against the heuristic bot, and $4 less against the Bayesian bot.

My first version, the one that wasted turns, was refused by the same references, with close gaps: +$1.11 and +$1.81 for the quiet v4c, +$1.82 for the reading exploiter with 5 players. The fix gains a little against the zoo (for example +$7.26 instead of +$6.91 against the marginal bot with 4 players), and loses a little against the reading exploiter with 5 players. These differences stay about as wide as the intervals.

## Why the quiet v4c does better

I broke down the gains of the selling v4c and of the quiet v4c against three recalibrated Hard bots, over 40 plain matches, minute by minute. Two things stand out.

In the first minute, the selling v4c also sells goal cards: 0.41 per round, at $7.33 on average. Each sale costs it a little money ($1.09 per round in all), and above all a card for the majority. It wins the majority in 47 % of rounds, against 55 % for the quiet v4c, and its majority share brings $9.33 less per round. Its non-goal sales in the first minute bring only $2.43 per round.

In the second minute, both make exactly the mistake that phase 5k wanted to avoid: about 1.5 non-goal cards per round, at $7.51 for the selling v4c and $9.40 for the quiet v4c, for a loss of $10 to $12 per round. Delaying the buys is not enough. The value that drives the buying is still too high once the first minute is over.

## What the reading exploiter takes from it with 5 players

I had the reading exploiter, the selling v4c and three recalibrated Hard bots play 40 matches of 10 rounds, in both seat orders. For each trade, I count what the seller gains on the buyer: the price minus the final value of the card ($10 if it is of the goal suit, $0 otherwise). What is left of each player's gain is its starting goal cards and its majority share, minus the ante.

| Seat order | reading exploiter gain | selling v4c gain | gap |
|---|---|---|---|
| reading exploiter first | +2.21 | +1.08 | +1.13 |
| selling v4c first | +7.07 | -1.51 | +8.58 |
| mean | +4.64 | -0.22 | +4.86 |

The reading exploiter comes out ahead in both orders, and the mean is close to the tournament gap (+$3.43). Yet the selling v4c wins on its trades with it: $5.48 per round on average. It also loses less than the reading exploiter against the Hard bots ($6.19 against $11.04). Everything happens in the rest: over the mean of both orders, the starting hands cancel out, and that rest brings $21.15 per round to the reading exploiter against $0.49 to the selling v4c. In other words, the reading exploiter overpays for its cards, but it takes the majority. The selling v4c, which buys nothing in the first minute and even sells goal cards, leaves it the majority.

It is the same flaw as against the recalibrated Hard bots, seen from another side: the selling v4c wins its trades, but loses the majority.

Does the bot progress? Not in the sense of the entry rule: the selling v4c is refused, and the marginal bot stays the reference bot. But it comes closer than the earlier candidates. Its worst gap at the mixed table is +$3.43 per round, against +$9.86 for the v4c and +$4.57 for the quiet v4c in phase 5j, on the same deals. And it beats both the marginal bot and the recalibrated Hard bot, with 4 and with 5 players, which neither the v4c nor the quiet v4c did in phase 5j. These gains are measured against simulated bots: they are not real gains on figgie.com.

Since it is refused with 4 players, I did not run the full tournament in the phase 5i format (300 deals, all references) that I had planned in case of success.

## Limits

The buy diagnostic uses plain matches, always in the same seat, without confidence intervals. Only the selling v4c was measured with duplicate deals, in the tournament. These plain matches and both diagnostics use scripts outside the repository.

The value the v4c gives a card in the first minute is too high, and I do not fix it: I only stop it from buying. Fixing the value itself, taking the time left into account, would be cleaner, and would cost a retraining.

The tournament is cut down like the phase 5j one: 100 deals instead of 300, and only part of the references. The intervals are about 1.7 times wider than in phase 5i.

Everything is still measured against simulated bots. These gains are not real gains on figgie.com.

## Reproduce

```bash
cd projets/bot-figgie
python3 -m unittest                                                  # the 135 tests, about 5 s
python3 -m figgie.tournoi --site --candidates v4c_vente_60 --rounds 10 --deals 100 --no-tables \
    --opponents heuristique sniper bayesien marginal hard_simule hard_simule_v2 --references \
    --mixed hard_simule_v2 bayesien marginal adaptatif_v3 adaptatif_v4b adaptatif_v4c v4c_calme_60 exploiteur \
        exploiteur_lecteur vendeur parieur --out tournoi.json
```

The tournament takes about 2 h 05 on 10 cores. To get back to the exact code of this phase: `git checkout phase5k-figgie`.
