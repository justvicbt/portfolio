# Phase 5b: playing against its own copies

*Version française : [phase5b.fr.md](phase5b.fr.md)*

Phase 5 ended on a precise flaw. The adaptive bot had learned on tables where the other players did not adapt. With several of them at the same table, its copies recognized the same situation, tightened their prices at the same moment, and a lone sniper profited. This phase fixes that flaw. It also adds three ideas I found by reading what others have written about Figgie.

The result is mixed. The new bot, v3, beats v2 and the marginal bot head to head, by a wider margin than before. Its copies are no longer exploited by the sniper, the marginal bot or the taker found in phase 5. But it still fails the minority test, for the same reasons as the marginal bot: the phase 4 exploiter and, with 4 players, the Bayesian bot make money against its copies. And the automatic search finds a new exploiter that takes $6.25 per round from it. No bot is promoted.

## What I read before starting

Before writing code, I read what exists about Figgie: the Jane Street video where two traders comment on three rounds, a thread on r/quant, David Jiang's lessons on theory-a.com, a Hacker News discussion, the posts by Rob Kohr, Logan Seaburg and Ross Rheingans-Yoo, the arXiv paper 2110.00879, several GitHub repositories of bots, and Rasmus Suonio's LinkedIn article, with his code and his game logs.

Several things the simulator assumed are confirmed. In the video, two players finish tied and split the rest of the pot: that is exactly the simulator's calculation. On Hacker News, a player says orders disappear after each trade, another rule assumed since phase 1. The traders in the video also do the same calculation as the marginal bot: the card that decides the majority is worth much more than $10.

Three ideas were not yet in our bots, and they became the first three steps of this phase.

1. **Counting cards with offered sales.** The idea comes from KnifeEdge, on r/quant. According to him, the site refuses a sell offer when you do not hold the card, and our simulator does the same. Whoever offers to sell a club therefore has at least one, even if they cancel the offer afterwards. Our counting only used trades.
2. **Playing with time.** This is the idea that comes up most: in the video, in David Jiang's lessons, in one of the repositories. The traders in the video take their time at the start and become aggressive in the last 40 seconds. Our bots quoted with the same spread from the first second to the last.
3. **Playing according to your hand.** The video and the Reddit thread both say it: a hand concentrated in one suit is played hard, a flat hand is played quietly.

## Step 1: a null result

The new counting is simple. A sell offer proves you hold at least one card of that suit. A purchase adds one. A sale removes one, if one was known. The test uses KnifeEdge's 5-player example: with 5 clubs in hand and what goes by on the market, we know there are at least 9 clubs in play, so 10 or 12.

I put this counting in a copy of the marginal bot, the "counter", and played it against the marginal bot on 400 duplicate deals (seed 2).

| | 4 players | 5 players |
|---|---|---|
| counter alone against corrected marginal | -0.78 [-1.91, +0.36] | -0.81 [-1.75, +0.14] |
| counter alone against marginal | +0.12 [-1.08, +1.32] | -1.48 [-2.67, -0.29] |
| marginal alone against counter | -0.15 [-1.28, +0.97] | +2.05 [+0.86, +3.25] |

In dollars per round, with the 95% confidence interval.

The counter does no better, and with 5 players it does slightly worse. The reason is arithmetic. With 10 cards in hand, almost everyone holds at least one card of each suit. Knowing that a player has "at least one" tells almost nothing. The rate of correctly guessed goal suit confirms it: 40.0% without the new counting, 40.1% with it, at a table of marginal bots. It does not change between 30 and 200 seconds either, because the market is already dead by then. I kept the code and the test, but the marginal bot stays the base.

## Step 2: a spread that tightens over time

The bot's spread and edge can now change during the round. They start from an initial value and move in a straight line to a final value at the last second. The test checks this on a bot going from an $8 spread to $2: early in the round it bids no more than $4; from 200 seconds on, it bids up to $9.

I tuned these two new numbers as in phase 2, on 150 tuning deals (seed 2), with 4 players, with the minority test. The criterion is the worst lower bound across all opponents. That criterion keeps the constant setting ($8, $1), with a worst bound of -8.0. But the table shows a trade-off:

| Setting (start → end) | against the sniper | against the reader | exploiter alone |
|---|---|---|---|
| spread 8 → 8, edge 1 → 1 | +13.5 | +0.3 | +5.9 |
| spread 8 → 3, edge 1 → 1 | +20.8 | +3.1 | +6.8 |

In dollars per round. The last column is the gain of the exploiter alone against copies of the bot.

Tightening at the end of the round earns clearly more against the sniper and the reader, but leaves a bit more to the exploiter. A final edge of $0 is worse everywhere. No fixed setting wins in every column. That is exactly the kind of choice the adaptive bot can make table by table. So I added two tightening settings, (8 → 3, 1 → 1) and (12 → 4, 3 → 1), to the four settings of phase 5.

## Step 3: training against its copies

This is the fix for the phase 5 flaw. The principle comes from game theory, under the name *fictitious play*: train the bot on tables where its previous versions play, then start again with the new version, until its choices stop changing.

In practice, each round of training draws 80 tables of 4 or 5 players. About one in two looks like the minority test: the whole table is made of copies of a previous version of the adaptive bot, except one player drawn from the league. The other tables are drawn from the league, previous versions included. On each table, I measure the six settings on 40 duplicate deals, in 3-round games. The first round does not count: the adaptive versions have not chosen their setting yet.

The bot also gets a new input: the strength of its hand. I compute the probability of each goal suit from my own deal alone. If the highest one exceeds 40%, the hand is "strong", which happens in about 23% of deals. Gains are measured separately for strong and flat hands.

I ran two training rounds. The first had v2 at the tables (seed 12), the second v2 and the v3 from the first round (seed 13). Each table is judged by a model built on the other 79:

| | Round 1 | Round 2 |
|---|---|---|
| fixed setting (8, 1) | +9.28 | +7.74 |
| chosen setting | +11.68 | +10.00 |
| gap to fixed | +2.40 [+1.91, +2.89] | +2.26 [+1.71, +2.80] |
| best setting, known afterwards | +12.60 | +11.25 |

In dollars per round. The choice recovers 64 to 72% of what one could win knowing the answer, against less than half for v2.

To see whether the choices settle, I looked at what the model picks on the minority-test-style tables, building it without the table being judged:

| Minority-style tables | Round 1 | Round 2 |
|---|---|---|
| flat hand | 8 → 3 on 36 tables, 12 → 4 on 7 | 8 → 3 on 37 tables, 12 → 4 on 3, others on 2 |
| strong hand | 8 → 3 on 22, 12 → 4 on 21 | 8 → 3 on 24, 12 → 4 on 18 |

The choices barely move from one round to the next, and neither does the gap to the fixed setting. I stopped after two rounds. With a flat hand, the bot keeps its $8 spread and tightens it to $3 at the end of the round. With a strong hand, it hesitates between that setting and a $12 spread that tightens to $4. The model from round 2 became v3's.

## The tournament

As in phase 5: 10-round games, 300 duplicate deals (seed 1), and both phase 4 exploiters in the minority test. The phase 5 taker is measured separately, on the same deals.

| | marginal | adaptive v2 | adaptive v3 |
|---|---|---|---|
| against marginal, 4 p. | | +2.00 [+1.64, +2.37] | +8.48 [+8.10, +8.87] |
| against marginal, 5 p. | | +3.47 [+3.15, +3.79] | +4.78 [+4.49, +5.07] |
| against sniper, 4 p. | +15.60 | +16.70 | +26.23 |
| against reader, 4 p. | +0.97 | +2.21 | +5.20 |
| against reader, 5 p. | +5.52 | +8.33 | +10.97 |
| against exploiter, 4 p. | +19.84 | +17.14 | +20.27 |
| sniper alone, 4 p. | -0.94 [-1.39, -0.48] | +3.72 [+3.24, +4.21] | -4.86 [-5.35, -4.37] |
| sniper alone, 5 p. | -1.28 [-1.64, -0.91] | +2.80 [+2.42, +3.19] | -0.27 [-0.64, +0.09] |
| marginal alone, 4 p. | | +1.29 [+0.95, +1.64] | -3.29 [-3.61, -2.98] |
| marginal alone, 5 p. | | -0.26 [-0.56, +0.04] | -2.34 [-2.61, -2.07] |
| taker alone, 4 p. | -0.70 [-1.11, -0.29] | +5.62 [+5.16, +6.08] | -9.87 [-10.28, -9.47] |
| taker alone, 5 p. | -1.30 [-1.69, -0.92] | +4.36 [+3.91, +4.80] | -4.17 [-4.59, -3.76] |
| Bayesian alone, 4 p. | +1.14 [+0.56, +1.72] | +0.10 [-0.47, +0.67] | +1.43 [+0.84, +2.02] |
| Bayesian alone, 5 p. | -0.61 [-1.00, -0.22] | -1.69 [-2.06, -1.33] | +0.27 [-0.12, +0.67] |
| exploiter alone, 4 p. | +4.32 [+3.85, +4.80] | +1.54 [+1.06, +2.02] | +5.27 [+4.83, +5.71] |
| exploiter alone, 5 p. | +7.24 [+6.85, +7.64] | +3.02 [+2.64, +3.39] | +7.79 [+7.46, +8.12] |

In dollars per round. The "alone" rows give the gain of the opponent alone against copies of the candidate: the higher it is, the more the candidate gets exploited.

Against the rest of the zoo, v3 wins clearly against every opponent, like the other two. At the abnormal tables (100 deals, 10 rounds), it does the same as v2: +$19.3 with the idle player, +$119.3 with the spammer and +$20.3 with the liars.

**The entry rule verdict.** v3 clearly beats the whole zoo, with 4 and 5 players. It fails the minority test with 4 players, because of the exploiter alone and the Bayesian alone, and with 5 players because of the exploiter alone. The marginal bot fails in exactly the same places. No bot is promoted, and the marginal bot stays the reference.

**Is the bot improving?** Head to head, yes, clearly: it earns more than v2 against every opponent, and four times more against the marginal bot with 4 players. Against exploiters, no, as the next section shows. The phase 5 flaw is fixed: the sniper, the marginal bot and the taker lost money against copies of the marginal bot, made money against copies of v2, and lose again against copies of v3, often more than against the marginal bot. On the other hand, v3 gives back to the phase 4 exploiter what v2 had taken away from it. Against that exploiter, it ends up at the marginal bot's level, slightly below.

## Why the exploiter still wins

I looked at the settings three copies of v3 choose against a lone opponent, over 20 games of 10 rounds. Against the sniper, they almost always take the $12 spread that tightens to $4, and the sniper then loses $4.86 per round. Against the exploiter, the marginal bot and the Bayesian bot, they almost always play $8 tightening to $3.

Against the exploiter, that choice is bad for the copies as a group. The step 2 table already showed it: the lone exploiter makes $6.8 against this setting, and $5.9 against the constant one. None of the settings I measured pushes it below zero. And since Figgie is zero-sum, its +$5.27 per round cost each of the three copies $1.76 on average.

Each copy still does what it was taught: it picks the setting that earns it the most, given what the others do. Self-play training finds exactly this kind of stable point, where nobody gains by changing alone. The minority test asks for something else: that the copies, together, leave nothing to the lone player. That is a team question, and nothing in the training asks it.

## Exploiters

I reran the phase 5 exploiter search against v3, under the same conditions: 4 players, 10-round games, 60 settings, then 20, 100 and 300 deals at the three stages (seeds 5, 6 and 1).

The winner is no longer a taker. It is a "tight quoter": it computes its values like the Bayesian bot, quotes with a spread of only $3, takes any quote that leaves it $3 of edge, and reacts in 0.2 seconds. Alone against three copies of v3, it makes +$6.25 per round [+5.71, +6.79]. I measured it against the other candidates, on the same 300 deals:

| Alone against copies of | taker (phase 5), 4 p. | taker, 5 p. | tight quoter (phase 5b), 4 p. | tight quoter, 5 p. |
|---|---|---|---|---|
| marginal | -0.70 [-1.11, -0.29] | -1.30 [-1.69, -0.92] | +4.95 [+4.43, +5.48] | +4.80 [+4.45, +5.15] |
| adaptive v2 | +5.62 [+5.16, +6.08] | +4.36 [+3.91, +4.80] | +1.49 [+1.01, +1.98] | +2.26 [+1.88, +2.64] |
| adaptive v3 | -9.87 [-10.28, -9.47] | -4.17 [-4.59, -3.76] | +6.25 [+5.71, +6.79] | +5.85 [+5.51, +6.20] |

Gain of the exploiter, in dollars per round.

This table looks like rock-paper-scissors. The taker beats v2, which resists the tight quoter. The tight quoter beats the marginal bot and v3, which resist the taker. Every candidate has an exploiter that takes $4 to $8 per round from it, counting the phase 4 exploiter too. v3 fixed v2's weakness and got the marginal bot's back. In the worst case, it is even the most exploitable of the three: $6.25 per round with 4 players and $7.79 with 5 (the phase 4 exploiter), against $4.95 and $7.24 for the marginal bot, $5.62 and $4.36 for v2.

## What I take away

What others wrote about Figgie gave me three ideas, and the most obvious one gave nothing. Counting offered sales looked clever. Yet the arithmetic showed in advance that with 10-card hands, knowing a player has "at least one" tells almost nothing.

The precise phase 5 flaw is fixed. Once trained against its own copies, the bot no longer throws itself into the price war that made the sniper and the taker win. Two rounds were enough for its choices to settle.

The two weaknesses in the tournament, the exploiter and the Bayesian bot alone, are not new. The marginal bot already had them, and against those opponents v3 plays almost like it. To fix them, I would need either a setting that denies the exploiter its gains, and none of those I measured does, or a training that judges the copies together.

The exploiter search shows the limit of the method. Each version fixes the weakness the previous one exposed, and opens another one. The marginal bot, v2 and v3 each have an exploiter that takes $4 to $8 per round from them. As long as the bot picks among a few fixed settings, an opponent who knows those settings always finds the one to counter. To get out of this, I would need a bot that mixes its settings at random, or whose value calculation leaves less to grab.

## Limits

All opponents are still bots. The gains measured here, against simulated bots, say nothing about the level against humans or against the site's bots.

Rasmus Suonio's logs, recorded on figgie.com, also show how far the simulator is from the real market. Over his 60 rounds, there are 53 trades per round on average, and almost half of them fall in the last minute. At our simulated tables, there are between 6 and 22, all in the first minute. The site also requires a new offer to beat the best current offer, whereas our simulator keeps one quote per player. A bot tuned on our tables is therefore tuned on a market that does not look like the site's.

The bot chooses among only six settings, and hand strength comes down to a single threshold. The two training rounds use 40 deals per table, in 3-round games. The tournament uses 300 deals, with intervals of about a dollar.

The limits of the previous phases still hold: made-up reaction times, money reset to $350 every round.

## Reproduce

```bash
cd projets/bot-figgie
python3 -m unittest                                                  # the 103 tests, about 10 s
python3 -m figgie.tune --players 4 --deals 150 --minority --spreads 8 10 12 --edges 1 \
    --spreads-late 3 5 8 --edges-late 1 0 --out reglage_temps_4j.json
python3 -m figgie.adapt --v3 1 --previous adaptatif_v2 --tables 80 --deals 40 --rounds 3 \
    --arms 6,3,6,3 8,1,8,1 10,3,10,3 12,3,12,3 8,1,3,1 12,3,4,1 --report entrainement_v3_1.json
python3 -m figgie.adapt --v3 2 --previous adaptatif_v2 adaptatif_v3_1 --tables 80 --deals 40 --rounds 3 \
    --arms 6,3,6,3 8,1,8,1 10,3,10,3 12,3,12,3 8,1,3,1 12,3,4,1 --report entrainement_v3_2.json
cp modeles/adaptation_v3_2.json modeles/adaptation_v3.json
python3 -m figgie.tournoi --candidates adaptatif_v3 --rounds 10 --deals 300 --table-deals 100 \
    --references heuristique sniper bayesien marginal exploiteur exploiteur_lecteur --out tournoi_v3.json
python3 -m figgie.exploit --target adaptatif_v3 --players 4 --rounds 10 --deals 20 100 300
```

Each training round takes about 50 minutes on 10 cores, the tournament two and a half hours. To get back exactly to this phase's code: `git checkout phase5b-figgie`.

## What next

Phase 6, the real site, still waits for written agreement from Jane Street. Before asking for it, I want results that mean something against the real market. The most useful next step is therefore to bring the simulator closer to the site: a simulated opponent calibrated on Rasmus Suonio's logs, the one-offer-per-side rule, and replaying real rounds. After that come an exact card-value calculation instead of Monte Carlo, new opponents, and a training that judges the copies together.
